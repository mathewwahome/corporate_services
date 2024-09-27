import frappe
from frappe import _

def finance_timesheet_submission(doc, method):
    if doc.workflow_state == "Approved by Finance":
        for timesheet in doc.timesheet_per_project:
            timesheet_doc = frappe.get_doc('Timesheet', timesheet.timesheet)
            if timesheet_doc.docstatus == 0:
                timesheet_doc.submit()
                frappe.msgprint(_("Timesheet {0} submitted successfully.").format(timesheet.timesheet))