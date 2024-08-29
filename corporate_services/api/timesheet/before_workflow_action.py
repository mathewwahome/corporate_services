import frappe
from frappe import _

def before_workflow_action_timesheet_submission(doc, method):

    if doc.docstatus == 0 and doc.workflow_state == "Submitted to Supervisor" and not doc.timesheet:
        frappe.throw(_("You must upload a timesheet before submitting to the supervisor."))
        frappe.msgprint(_("You must upload a timesheet before submitting to the supervisor"))