import frappe


import frappe

def alert_supervisor_travel_request(doc, method):
    # Get the employee
    employee_id = doc.employee
    employee = frappe.get_doc("Employee", employee_id)
    
    # Get the supervisor (Report To)
    if employee.reports_to:
        supervisor_id = employee.reports_to
        supervisor = frappe.get_doc("Employee", supervisor_id)
        
        # Determine supervisor email
        supervisor_email = supervisor.company_email or supervisor.personal_email
        message = """
            Dear {},

            I have submitted my {} for your review and approval.
        
            Best regards,
            
            The Example Team
            """.format(supervisor.employee_name, doc.doctype)
        
        # Send email
        response = frappe.sendmail(
            recipients=[supervisor_email],
            subject=frappe._('Travel Request Submission from {}'.format(employee.employee_name)),
            message=message,
            sender="apps@intellisoftkenya.com",
            is_html=False
        )
        return response




# The leave application notification
def alert_supervisor_leave_application(doc, method):
    
    # get the employee
    employee_id = doc['employee']
    employee = frappe.get_doc("Employee", employee_id)
    
    # get the supervisor (Report To)
    supervisor_id = employee['reports_to']
    supervisor = frappe.get_doc("Employee", supervisor_id)
    
    supervisor_email = supervisor['company_email'] or supervisor['personal_email']
    message = """
        Dear {},

        I have applied for leave starting from {} to {}. Please review and approve it accordingly.
    
        Kind regards,
        
        {}
        """.format(supervisor['employee_name'], doc["from_date"], doc["to_date"], employee["employee_name"])
    
    response = frappe.sendmail(
        recipients=[supervisor_email],
        subject=frappe._('Leave Application Submission from {}'.format(employee['employee_name'])),
        message=message,
        sender="apps@intellisoftkenya.com",
        is_html=False
    )
    return response
