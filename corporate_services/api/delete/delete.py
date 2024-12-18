import frappe

def delete_all_timesheet_submissions():
      # Retrieve all Timesheet records
    timesheets = frappe.get_all('Timesheet', fields=['name', 'status'])

    for timesheet in timesheets:
        if timesheet['status'] == 'Submitted':
            try:
                # Fetch the timesheet document
                timesheet_doc = frappe.get_doc('Timesheet', timesheet['name'])
                
                # Attempt to cancel the timesheet if it's submitted
                timesheet_doc.cancel()
                frappe.msgprint(f"Timesheet {timesheet['name']} has been canceled.")
            except frappe.PermissionError:
                # If permission error occurs, skip this timesheet
                frappe.msgprint(f"Permission error: Unable to cancel Timesheet {timesheet['name']}.")
            except Exception as e:
                # Log any other errors that occur
                frappe.msgprint(f"Error while canceling Timesheet {timesheet['name']}: {str(e)}")
        else:
            frappe.msgprint(f"Timesheet {timesheet['name']} is not submitted, skipping cancellation.")
        
        # After attempting to cancel, force delete the timesheet
        try:
            frappe.delete_doc('Timesheet', timesheet['name'], force=True)
            frappe.msgprint(f"Timesheet {timesheet['name']} has been force deleted.")
        except Exception as e:
            frappe.msgprint(f"Error while deleting Timesheet {timesheet['name']}: {str(e)}")
