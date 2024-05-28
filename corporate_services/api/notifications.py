import frappe


def alert_supervisor(doc):
    
    # get the employee
    employee_id = doc['employee']
    employee = frappe.get_doc("Employee", employee_id)
    
    # get the supervisor (Report To)
    supervisor_id = employee['reports_to']
    supervisor = frappe.get_doc("Employee", supervisor_id)
    
    supervisor_email = supervisor['company_email'] or supervisor['personal_email']
    message = """
        Dear {},

        I have submitted my {} for your review and approval.
    
        Best regards,
        
        The Example Team
        """.format(supervisor['employee_name'], doc["doctype"], doc["name"])
    
    response = frappe.sendmail(
        recipients=[supervisor_email],
        subject=frappe._('Travel Request Submission from {}'.format(employee['employee_name'])),
        message=message,
        sender="apps@intellisoftkenya.com",
        is_html=False
    )
    return response
    