import frappe
from frappe.utils import get_url_to_form, now_datetime

def send_email(recipients, subject, message, pdf_content, doc_name):
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=[{
            'fname': '{}.pdf'.format(doc_name),
            'fcontent': pdf_content
        }],
        header=("Staff Requisition", "text/html")
    )

def generate_message(doc, employee_name, email_type):
    doctype_url = get_url_to_form(doc.doctype, doc.name)
    messages = {
        "submitted_to_hr": """
            Dear HR,<br><br>
            {}, {} has been submitted for your review. You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            System
        """.format(employee_name, doc.doctype, doctype_url),

        "submitted_to_finance": """
            Dear Finance,<br><br>
            {}, {} has been reviewed and approved by HR. You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            HR
        """.format(employee_name, doc.doctype, doctype_url),
    }
    return messages[email_type]

def alert(doc, method):
    if doc.flags.in_alert:
        return
    
    if doc.workflow_state in ["Submitted to HR", "Submitted to Finance"]:
        # Get requestor employee details
        requestor_id = doc.requestor
        requestor = frappe.get_doc("Employee", requestor_id)
        requestor_name = requestor.employee_name
        
        print_format = "Standard"
        pdf_content = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)

        if doc.workflow_state == "Submitted to HR":
            hr_managers = frappe.get_all('Has Role', filters={'role': 'HR Manager'}, fields=['parent'])
            hr_manager_emails = [frappe.get_value('User', hr_manager.parent, 'email') for hr_manager in hr_managers]
            
            message_to_hr = generate_message(doc, requestor_name, "submitted_to_hr")
            send_email(
                recipients=hr_manager_emails,
                subject=frappe._('Staff Requisition from {}'.format(requestor_name)),
                message=message_to_hr,
                pdf_content=pdf_content,
                doc_name=doc.name
            )
          
        elif doc.workflow_state == "Submitted to Finance":
            # Check if HR approval already exists to prevent duplicate entries
            hr_approval_exists = any(
                row.title == 'HR' 
                for row in doc.staff_requisition_approval
            )
            
            if not hr_approval_exists:
                # Add approval record to child table
                doc.append('staff_requisition_approval', {
                    'title': 'HR',
                    'employee_name': frappe.session.user,
                    'datetime': now_datetime()
                })
                
                doc.flags.in_alert = True
                doc.save(ignore_permissions=True)
            
            finance_team = frappe.get_all('Has Role', filters={'role': 'Finance'}, fields=['parent'])
            finance_team_emails = [frappe.get_value('User', finance_manager.parent, 'email') for finance_manager in finance_team]
            
            message_to_finance = generate_message(doc, requestor_name, "submitted_to_finance")
            send_email(
                recipients=finance_team_emails,
                subject=frappe._('Staff Requisition from {}'.format(requestor_name)),
                message=message_to_finance,
                pdf_content=pdf_content,
                doc_name=doc.name
            )

doc_events = {
    "Staff Requisition": {
        "on_update": alert
    }
}