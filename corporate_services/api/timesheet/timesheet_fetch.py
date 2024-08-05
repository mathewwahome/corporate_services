import frappe

@frappe.whitelist()
def fetch_timesheets_for_employee(employee_id, month):
    try:
        timesheets = frappe.get_all('Timesheet', 
                                    filters={'employee': employee_id, 'custom_month': month}, 
                                    fields=['name', 'custom_project_name', 'custom_month', 'total_hours', 'status'])
        return timesheets
    except Exception as e:
        frappe.log_error(f"Error fetching timesheets for employee {employee_id}: {str(e)}", "fetch_timesheets_for_employee")
        return []

@frappe.whitelist()
def fetch_internal_timesheet(employee_id, month):
    try:
        timesheet = frappe.get_all('Internal Timesheet', 
                                    filters={'employee': employee_id, 'month': month}, 
                                    fields=['name', 'month', 'status'],
                                    limit=1)
        frappe.log_error(f"internal timesheet for employee {timesheet}", "fetch_internal_timesheet")
        
        return timesheet[0] if timesheet else None
    except Exception as e:
        frappe.log_error(f"Error fetching internal timesheet for employee {employee_id}: {str(e)}", "fetch_internal_timesheet")
        return None