import frappe
from frappe import _

def before_workflow_action_timesheet_submission(doc, method):
    if doc.workflow_state == "Submitted to Supervisor":
        frappe.throw(_("You must upload a timesheet before submitting to the supervisor for {0}.").format(doc.name))

