import frappe
from frappe.utils import get_fullname, get_url_to_form

@frappe.whitelist()
def send_clarification_email(docname, message):
    """
    Sends a clarification request email to the requester of a Staff Requisition.
    """
    doc = frappe.get_doc("Staff Requisition", docname)

    if not doc.requestor:
        frappe.throw("Staff Requisition has no requestor assigned.")

    requestor = frappe.get_doc("Employee", doc.requestor)

    recipient_email = requestor.company_email or requestor.personal_email
    if not recipient_email:
        frappe.throw(f"No email found for requestor {requestor.employee_name}.")

    approver_name = get_fullname(frappe.session.user)

    doc_url = get_url_to_form(doc.doctype, doc.name)
    email_message = f"""
    Hello {requestor.employee_name},<br><br>
    {approver_name} has requested clarification on Staff Requisition {doc.name}.<br><br>
    Clarification Details:<br>
    {message}<br><br>
    You can view the request here: <a href="{doc_url}">{doc.name}</a><br><br>
    Regards,<br>
    HR System
    """

    frappe.sendmail(
        recipients=[recipient_email],
        subject=f"Clarification Requested for {doc.name}",
        message=email_message
    )

    return "Clarification email sent successfully."
