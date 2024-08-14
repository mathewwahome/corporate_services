import frappe

def update_timesheet_workflow(doc, method):
    if doc.workflow_state == 'Submitted':
        timesheets = frappe.get_all('Timesheet', filters={'timesheet_submission': doc.name})

        for timesheet in timesheets:
            frappe.db.set_value('Timesheet', timesheet.name, 'workflow_state', 'Submitted to Supervisor')
            timesheet_doc = frappe.get_doc('Timesheet', timesheet.name)
            if timesheet_doc.docstatus == 0:
                timesheet_doc.submit()
                
        frappe.db.commit()
