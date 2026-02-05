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

def get_user_full_name(email):
    """Get the full name of a user from their email"""
    return frappe.get_value('User', email, 'full_name') or email

def generate_message(doc, employee_name, email_type, recipient_email):
    doctype_url = get_url_to_form(doc.doctype, doc.name)
    recipient_name = get_user_full_name(recipient_email)
    
    messages = {
        "submitted_to_hr": """
            Dear {},<br><br>
            {}, {} has been submitted for your review. You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            System
        """.format(recipient_name, employee_name, doc.doctype, doctype_url),

        "submitted_to_finance": """
            Dear {},<br><br>
            {}, {} has been reviewed and approved by HR. You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            HR
        """.format(recipient_name, employee_name, doc.doctype, doctype_url),
        
        "submitted_to_ceo": """
            Dear {},<br><br>
            {}, {} has been reviewed and approved by Finance. You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            Finance
        """.format(recipient_name, employee_name, doc.doctype, doctype_url),
        
        "approved_by_ceo": """
            Dear {},<br><br>
            {}, {} has been approved by the CEO. You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            CEO
        """.format(recipient_name, employee_name, doc.doctype, doctype_url)
    }
    return messages[email_type]

def get_users_with_role(role):
    """Get email addresses of all users with a specific role"""
    users = frappe.get_all('Has Role', filters={'role': role}, fields=['parent'])
    return [frappe.get_value('User', user.parent, 'email') for user in users]

def add_approval_if_not_exists(doc, title):
    """Add approval entry if it doesn't already exist"""
    approval_exists = any(row.title == title for row in doc.staff_requisition_approval)
    
    if not approval_exists:
        doc.append('staff_requisition_approval', {
            'title': title,
            'employee_name': frappe.session.user,
            'datetime': now_datetime()
        })
        doc.flags.in_alert = True
        doc.save(ignore_permissions=True)

def alert(doc, method):
    if doc.flags.in_alert:
        return
    
    if doc.workflow_state not in ["Submitted to HR", "Submitted to Finance", "Submitted to CEO", "Approved by CEO"]:
        return
    
    requestor = frappe.get_doc("Employee", doc.requestor)
    requestor_name = requestor.employee_name
    
    pdf_content = frappe.get_print(doc.doctype, doc.name, "Standard", as_pdf=True)
    
    workflow_config = {
        "Submitted to HR": {
            "recipients": get_users_with_role('HR Manager'),
            "message_type": "submitted_to_hr",
            "approval_title": "Requestor"
            
        },
        "Submitted to Finance": {
            "recipients": get_users_with_role('Finance'),
            "message_type": "submitted_to_finance",
            "approval_title": "HR"
        },
        "Submitted to CEO": {
            "recipients": get_users_with_role('CEO'),
            "message_type": "submitted_to_ceo",
            "approval_title": "Finance"
        },
        "Approved by CEO": {
            "recipients": get_users_with_role('HR Manager'),
            "message_type": "approved_by_ceo",
            "approval_title": "CEO"
        }
    }
    
    config = workflow_config[doc.workflow_state]
    
    if "approval_title" in config:
        add_approval_if_not_exists(doc, config["approval_title"])
    
    for recipient_email in config["recipients"]:
        message = generate_message(doc, requestor_name, config["message_type"], recipient_email)
        send_email(
            recipients=[recipient_email],
            subject=frappe._('Staff Requisition from {}'.format(requestor_name)),
            message=message,
            pdf_content=pdf_content,
            doc_name=doc.name
        )

doc_events = {
    "Staff Requisition": {
        "on_update": alert
    }
}