import frappe
from frappe.utils import get_fullname, get_url_to_form

@frappe.whitelist()
def send_clarification_email(docname, message):
    """
    Sends a clarification request email + system notification to the
    requester of a Staff Requisition, and transitions workflow to Needs Clarification.
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

    # Transition workflow state before sending notifications
    doc.workflow_state = "Needs Clarification"
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    email_message = f"""
    Hello {requestor.employee_name},<br><br>
    {approver_name} has requested clarification on Staff Requisition 
    <b>{doc.name}</b> before it can proceed further.<br><br>
    <b>Clarification Required:</b><br>
    {message}<br><br>
    Please review the requisition and resubmit once the clarification has been addressed.<br><br>
    <a href="{doc_url}" style="background-color:#FF5722; color:white; padding:10px 20px;
    text-decoration:none; border-radius:5px; display:inline-block;">
    View &amp; Resubmit
    </a><br><br>
    Regards,<br>
    HR Management
    """

    frappe.sendmail(
        recipients=[recipient_email],
        subject=f"Clarification Required – {doc.name}",
        message=email_message
    )

    # System notification (ERP inbox)
    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": f"Clarification Required on {doc.name}",
        "email_content": f"{approver_name} has requested clarification: {message}",
        "for_user": recipient_email,
        "type": "Alert",
        "document_type": doc.doctype,
        "document_name": doc.name,
        "from_user": frappe.session.user
    }).insert(ignore_permissions=True)

    # Audit trail comment on the document
    doc.add_comment(
        "Comment",
        f"Workflow moved to <b>Needs Clarification</b> by {approver_name}.<br>"
        f"<b>Reason:</b> {message}"
    )

    return "Clarification email sent and workflow updated to Needs Clarification."