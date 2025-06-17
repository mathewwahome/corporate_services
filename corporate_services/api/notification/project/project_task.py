import frappe
from frappe.utils import get_url_to_form
from frappe import _

def send_task_email(recipients, subject, message, doc_name):
    """Send email notification for task allocation"""
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            header=("Task Notification", "text/html")
        )
        return True
    except Exception as e:
        frappe.log_error(f"Error sending email: {str(e)}", "Task Email Error")
        return False

def generate_task_message(doc, employee_name, employee_email):
    """Generate email message for task allocation"""
    doctype_url = get_url_to_form(doc.doctype, doc.name)
    
    message = """
        Dear {},<br><br>
        You have been allocated a new task: <strong>{}</strong><br><br>
        <strong>Task Details:</strong><br>
        - Task Name: {}<br>
        - Description: {}<br>
        - Priority: {}<br>
        - Status: {}<br>
        - Expected Start Date: {}<br>
        - Expected End Date: {}<br>
    """.format(
        employee_name,
        doc.subject or "New Task",
        doc.subject or "No subject",
        doc.description or "No description provided",
        doc.priority or "Medium",
        doc.status or "Open",
        doc.exp_start_date or "Not specified",
        doc.exp_end_date or "Not specified"
    )
    
    if doc.project:
        project_url = get_url_to_form("Project", doc.project)
        message += """
        - Project: <a href="{}">{}</a><br>
        """.format(project_url, doc.project)
    
    message += """
        <br>
        You can view and manage this task by clicking <a href="{}">here</a>.<br><br>
        Please review the task details and update the status accordingly.<br><br>
    """.format(doctype_url)
    
    return message

def task_on_update(doc, method):
    """Handle task updates - send email after save/update when conditions are met"""
    
    # Only proceed if send_email is checked and allocate_to is set
    if not (doc.custom_send_email and doc.custom_allocate_to):
        return
    
    # Check if email was already sent
    if doc.custom_email_sent:
        return
    
    try:
        # Get employee details
        employee = frappe.get_doc("Employee", doc.custom_allocate_to)
        employee_email = employee.company_email or employee.personal_email
        employee_name = employee.employee_name
        
        if not employee_email:
            frappe.log_error(f"Employee {employee_name} does not have an email address", "Task Email Error")
            return
        
        message = generate_task_message(doc, employee_name, employee_email)
        
        email_sent = send_task_email(
            recipients=[employee_email],
            subject=frappe._('New Task Allocated: {}'.format(doc.subject or doc.name)),
            message=message,
            doc_name=doc.name
        )
        
        if email_sent:
            frappe.db.sql("""
                UPDATE `tabTask` 
                SET custom_email_sent = 1, custom_email_sent_date = NOW() 
                WHERE name = %s
            """, doc.name)
            frappe.db.commit()
            
        
    except Exception as e:
        frappe.log_error(f"Error in task_on_update: {str(e)}", "Task Email Notification Error")
        frappe.publish_realtime(
            "msgprint",
            {
                "message": f"Failed to send email: {str(e)}",
                "title": "Email Error", 
                "indicator": "red"
            },
            user=frappe.session.user
        )