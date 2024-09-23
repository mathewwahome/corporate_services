import frappe
from frappe.utils import get_url_to_form
from frappe import _

def send_email(recipients, subject, message, pdf_content, doc_name):
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=[{
            'fname': '{}.pdf'.format(doc_name),
            'fcontent': pdf_content
        }],
        header=("Supplier Quote Submission", "text/html")
    )

def generate_message(doc, employee_name, email_type, supervisor_name=None):
    doctype_url = get_url_to_form(doc.doctype, doc.name)
    messages = {
        "quote_submission": """
            Dear {},<br><br>
            I have submitted my {} for your review and approval. You can view it <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            {}
        """.format(supervisor_name, doc.doctype, doctype_url, employee_name),

    }
    return messages[email_type]

def alert(doc, method):
    
   
    employee_id = doc.requested_by
    employee = frappe.get_doc("Employee", employee_id)
    employee_email = employee.company_email or employee.personal_email
    print_format = "Standard"
    pdf_content = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)
         
    message_to_employee = generate_message(doc, employee.employee_name, "employee_rejected_finance")
    send_email(
        recipients=[employee_email],
        subject=frappe._('Your Asset Requisition has been Rejected by Finance'),
        message=message_to_employee,
        pdf_content=pdf_content,
        doc_name=doc.name
    )
    hr_managers = frappe.get_all('Has Role', filters={'role': 'HR Manager'}, fields=['parent'])
    hr_manager_emails = [frappe.get_value('User', hr_manager.parent, 'email') for hr_manager in hr_managers]
    message_to_hr = generate_message(doc, employee.employee_name, "quote_submission")
    send_email(
        recipients= hr_manager_emails,
        subject=frappe._('Asset Requisition Rejected by Finance'),
        message=message_to_hr,
        pdf_content=pdf_content,
        doc_name=doc.name
    )

doc_events = {
    "Supplier Quote Submission": {
        "on_update": alert
    }
}
