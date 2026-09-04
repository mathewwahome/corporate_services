from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_datetime, get_url_to_form, now_datetime

from corporate_services.api.notification.notification_contacts import (
	get_employee_contact,
	get_supervisor_contact,
)

LOG_DOCTYPE = "Reminder Log"
DISPATCH_LOG_DOCTYPE = "Notification Dispatch Log"

SUBMITTER_RESOLVERS = {}
APPROVER_RESOLVERS = {}


def _resolve_fixed_field_contact(value):
	if not value:
		return None
	if frappe.db.exists("Employee", value):
		return get_employee_contact(value)
	if frappe.db.exists("User", value):
		user = frappe.get_doc("User", value)
		return frappe._dict(user_id=user.name, email=user.email, name=user.full_name or user.name)
	return None


def _generic_submitter_contact(rule, doc):
	if not rule.employee_field:
		return None
	return get_employee_contact(doc.get(rule.employee_field))


def _generic_approver_contacts(rule, doc):
	if rule.approver_type == "Fixed Field on Document":
		contact = _resolve_fixed_field_contact(doc.get(rule.approver_field)) if rule.approver_field else None
	else:
		employee_name = doc.get(rule.employee_field) if rule.employee_field else None
		contact = get_supervisor_contact(frappe.get_doc("Employee", employee_name)) if employee_name else None
	return [contact] if contact and contact.email else []


def _resolve_submitter(rule, doc):
	resolver = SUBMITTER_RESOLVERS.get(rule.reference_doctype)
	return resolver(doc) if resolver else _generic_submitter_contact(rule, doc)


def _resolve_approvers(rule, doc):
	resolver = APPROVER_RESOLVERS.get(rule.reference_doctype)
	return resolver(doc) if resolver else _generic_approver_contacts(rule, doc)


def get_active_rules():
	config = frappe.get_single("HR Config")
	return [row for row in (config.reminder_rules or []) if row.enabled]


def get_rule(reference_doctype, workflow_state):
	for row in get_active_rules():
		if row.reference_doctype == reference_doctype and row.pending_workflow_state == workflow_state:
			return row
	return None


def get_state_entered_at(doc, workflow_state):
	entered_at = frappe.db.get_value(
		DISPATCH_LOG_DOCTYPE,
		{
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"workflow_state": workflow_state,
		},
		"min(sent_on)",
	)
	return get_datetime(entered_at) if entered_at else get_datetime(doc.modified)


def _already_sent(doc, workflow_state, event_type, recipient):
	return frappe.db.exists(
		LOG_DOCTYPE,
		{
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"workflow_state": workflow_state,
			"event_type": event_type,
			"recipient": recipient,
		},
	)


def _log_event(doc, workflow_state, event_type, recipient, triggered_by=None):
	frappe.get_doc(
		{
			"doctype": LOG_DOCTYPE,
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"workflow_state": workflow_state,
			"event_type": event_type,
			"recipient": recipient,
			"triggered_by": triggered_by,
			"sent_on": now_datetime(),
		}
	).insert(ignore_permissions=True)


def _send(doc, contact, subject, message):
	if not contact or not contact.email:
		return False
	frappe.sendmail(recipients=[contact.email], subject=subject, message=message)

	if contact.get("user_id") and frappe.db.exists("User", contact.user_id):
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": subject,
					"email_content": message,
					"for_user": contact.user_id,
					"type": "Alert",
					"document_type": doc.doctype,
					"document_name": doc.name,
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Reminder engine: Notification Log failed")

	return True


def check_overdue_documents():
	"""Scheduled entrypoint: notify submitters/approvers of pending documents
	that have breached their configured Reminder Rule SLA."""
	for rule in get_active_rules():
		pending_docs = frappe.get_all(
			rule.reference_doctype,
			filters={"workflow_state": rule.pending_workflow_state, "docstatus": ["!=", 2]},
			pluck="name",
		)
		for name in pending_docs:
			try:
				_process_overdue(rule, name)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					f"Reminder engine failed for {rule.reference_doctype} {name}",
				)


def _process_overdue(rule, name):
	doc = frappe.get_doc(rule.reference_doctype, name)
	if doc.workflow_state != rule.pending_workflow_state:
		return

	entered_at = get_state_entered_at(doc, rule.pending_workflow_state)
	if now_datetime() < entered_at + timedelta(hours=rule.sla_hours):
		return

	doctype_url = get_url_to_form(doc.doctype, doc.name)

	if rule.notify_submitter_on_breach:
		submitter = _resolve_submitter(rule, doc)
		if submitter and submitter.email and not _already_sent(
			doc, doc.workflow_state, "Breach Notice", submitter.email
		):
			message = (
				f"Dear {submitter.name},<br><br>"
				f"Your {doc.doctype} ({doc.name}) has not yet been reviewed by your approver. "
				f'You can view it <a href="{doctype_url}">here</a> and resurface it to them for a review.<br><br>'
				"Kind regards,<br>System"
			)
			if _send(doc, submitter, _("Your {0} is awaiting review").format(doc.doctype), message):
				_log_event(doc, doc.workflow_state, "Breach Notice", submitter.email)

	if rule.auto_remind_approver:
		for approver in _resolve_approvers(rule, doc):
			if approver.email and not _already_sent(
				doc, doc.workflow_state, "Auto Remind Approver", approver.email
			):
				message = (
					f"Dear {approver.name},<br><br>"
					f"A {doc.doctype} ({doc.name}) has been awaiting your review for over "
					f'{rule.sla_hours} hours. Please review it <a href="{doctype_url}">here</a>.<br><br>'
					"Kind regards,<br>System"
				)
				if _send(
					doc, approver, _("Reminder: {0} awaiting your review").format(doc.doctype), message
				):
					_log_event(doc, doc.workflow_state, "Auto Remind Approver", approver.email)


@frappe.whitelist()
def resurface_approver(reference_doctype, reference_name):
	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("read")

	rule = get_rule(reference_doctype, doc.workflow_state)
	if not rule or not rule.allow_submitter_resurface:
		frappe.throw(_("Resurfacing is not enabled for {0} in its current state.").format(reference_doctype))

	submitter = _resolve_submitter(rule, doc)
	if (not submitter or submitter.user_id != frappe.session.user) and not frappe.has_permission(
		reference_doctype, "write", doc, user=frappe.session.user
	):
		frappe.throw(_("Only the submitter can resurface this to the approver."), frappe.PermissionError)

	approvers = _resolve_approvers(rule, doc)
	if not approvers:
		frappe.throw(_("No approver could be resolved for this document."))

	cooldown_hours = rule.resurface_cooldown_hours or 0
	last_resurfaced = frappe.db.get_value(
		LOG_DOCTYPE,
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"workflow_state": doc.workflow_state,
			"event_type": "Employee Resurface",
		},
		"max(sent_on)",
	)
	if last_resurfaced and cooldown_hours:
		next_allowed = get_datetime(last_resurfaced) + timedelta(hours=cooldown_hours)
		if now_datetime() < next_allowed:
			remaining = next_allowed - now_datetime()
			hours, remainder = divmod(int(remaining.total_seconds()), 3600)
			minutes = remainder // 60
			return {
				"success": False,
				"message": _("You can resurface this again in {0}h {1}m.").format(hours, minutes),
			}

	doctype_url = get_url_to_form(doc.doctype, doc.name)
	submitter_name = submitter.name if submitter else frappe.session.user
	sent_to = []
	for approver in approvers:
		message = (
			f"Dear {approver.name},<br><br>"
			f"{submitter_name} is resurfacing their {doc.doctype} ({doc.name}) for your review. "
			f'You can view it <a href="{doctype_url}">here</a>.<br><br>'
			f"Kind regards,<br>{submitter_name}"
		)
		if _send(doc, approver, _("Reminder: please review {0}").format(doc.name), message):
			_log_event(
				doc, doc.workflow_state, "Employee Resurface", approver.email, triggered_by=frappe.session.user
			)
			sent_to.append(approver.name)

	if not sent_to:
		frappe.throw(_("Could not reach the approver - no email on file."))

	return {"success": True, "message": _("Reminder sent to {0}.").format(", ".join(sent_to))}
