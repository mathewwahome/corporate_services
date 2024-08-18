import frappe
from frappe import _

def before_workflow_action_timesheet_submission(doc, method):
    if doc.workflow_state == "Submitted to Supervisor" and not doc.timesheet:
        frappe.throw(_("You must upload a timesheet before submitting to the supervisor."))


doc_events = {
    "Timesheet Submission": {
        "before_workflow_action": "corporate_services.api.timesheet.before_workflow_action.before_workflow_action_timesheet_submission",
    }
}
