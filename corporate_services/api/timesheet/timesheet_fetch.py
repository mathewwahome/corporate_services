import frappe
from frappe.utils import flt

@frappe.whitelist()
def fetch_timesheets_for_employee(employee_id, month):
    try:
        timesheets = frappe.get_all('Timesheet', 
                                    filters={'employee': employee_id, 'custom_month': month}, 
                                    fields=['name', 'custom_project_name', 'parent_project', 'custom_month', 'total_hours', 'custom_timesheet_type', 'status'])
        
        total_hours_for_month = sum(flt(timesheet.total_hours) for timesheet in timesheets)
        
        employee = frappe.get_doc('Employee', employee_id)
        monthly_gross_pay = flt(employee.ctc)
        
        total_hours_accumulated = 0
        
        for timesheet in timesheets:
            project_hours = flt(timesheet.total_hours)
            total_hours_accumulated += project_hours
            
            if total_hours_for_month > 0:
                percent_pay = (project_hours / total_hours_for_month) * 100
            else:
                percent_pay = 0
            
            pay_for_project = (percent_pay / 100) * monthly_gross_pay
            
            timesheet.update({
                'percent_pay': round(percent_pay, 2),
                'pay_for_project': round(pay_for_project, 2),
                'total_hours_accumulated': total_hours_accumulated
            })
        
        return {
            'timesheets': timesheets,
            'total_working_hours': total_hours_accumulated
        }
    except Exception as e:
        frappe.log_error(f"Error fetching timesheets for employee {employee_id}: {str(e)}", "fetch_timesheets_for_employee")
        return []