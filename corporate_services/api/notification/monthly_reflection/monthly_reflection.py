import frappe
from frappe.utils import get_url_to_form
from corporate_services.api.helpers.print_formats import get_default_print_format
from corporate_services.api.notification.notification_contacts import (
    get_hr_manager_emails,
    get_supervisor_contact,
)


def build_email_body(greeting, intro, action_line, link_url, sign_off, signer):
    return """
        <p>{greeting},</p>
        <p>{intro}</p>
        <p>{action_line} <a href="{link}">Click here to view it</a>.</p>
        <br>
        <p>Kind regards,<br><strong>{signer}</strong></p>
    """.format(
        greeting=greeting,
        intro=intro,
        action_line=action_line,
        link=link_url,
        signer=signer,
    )


def generate_message(doc, employee_name, supervisor_name, email_type):
    url = get_url_to_form(doc.doctype, doc.name)
    doctype_label = doc.doctype

    templates = {
        "supervisor": build_email_body(
            greeting="Dear {}".format(supervisor_name),
            intro="{} has submitted a {} for your review and acknowledgement.".format(employee_name, doctype_label),
            action_line="Please review the reflection at your earliest convenience.",
            link_url=url,
            sign_off="Kind regards",
            signer=employee_name,
        ),
        "employee_acknowledged": build_email_body(
            greeting="Dear {}".format(employee_name),
            intro="Good news! Your {} has been reviewed and acknowledged by your supervisor.".format(doctype_label),
            action_line="You can view the acknowledged reflection at any time.",
            link_url=url,
            sign_off="Kind regards",
            signer="Your Supervisor",
        ),
        "employee_rejected": build_email_body(
            greeting="Dear {}".format(employee_name),
            intro="Your {} has been reviewed and returned by your supervisor for revision.".format(doctype_label),
            action_line="Please review the details and make the necessary updates.",
            link_url=url,
            sign_off="Kind regards",
            signer="Your Supervisor",
        ),
        "hr_submitted": build_email_body(
            greeting="Dear HR Manager",
            intro="{}'s Monthly Reflection has been acknowledged by their supervisor and submitted to HR.".format(employee_name),
            action_line="Please review the reflection at your earliest convenience.",
            link_url=url,
            sign_off="Kind regards",
            signer=employee_name,
        ),
        "employee_hr_approved": build_email_body(
            greeting="Dear {}".format(employee_name),
            intro="Your {} has been fully reviewed and approved by HR.".format(doctype_label),
            action_line="You can view the approved reflection at any time.",
            link_url=url,
            sign_off="Kind regards",
            signer="HR Manager",
        ),
        "employee_hr_rejected": build_email_body(
            greeting="Dear {}".format(employee_name),
            intro="Your {} has been reviewed by HR and returned for revision.".format(doctype_label),
            action_line="Please review the comments and make the necessary updates.",
            link_url=url,
            sign_off="Kind regards",
            signer="HR Manager",
        ),
    }

    return templates[email_type]


def send_email(recipients, subject, message, pdf_content, doc_name):
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=[{
            "fname": "{}.pdf".format(doc_name),
            "fcontent": pdf_content,
        }],
        header=("Monthly Reflection", "text/html"),
    )


def add_user_permission(user, employee_id):
    """
    Add User Permission so supervisor can access records 
    linked to this employee — same mechanism as Leave Application.
    """
    if not user or not employee_id:
        return

    if frappe.db.exists("User Permission", {
        "user": user,
        "allow": "Employee",
        "for_value": employee_id,
    }):
        return

    perm = frappe.get_doc({
        "doctype": "User Permission",
        "user": user,
        "allow": "Employee",
        "for_value": employee_id,
        "apply_to_all_doctypes": 0,
        "applicable_for": "Monthly Reflection",
    })
    perm.insert(ignore_permissions=True)
    frappe.db.commit()


def alert(doc, method):
    WATCHED_STATES = {
        "Submitted to Supervisor",
        "Acknowledged by Supervisor",
        "Returned by Supervisor",
        "Submitted to HR",
        "Approved by HR",
        "Rejected By HR",
    }

    if doc.workflow_state not in WATCHED_STATES:
        return

    employee = frappe.get_doc("Employee", doc.employee)
    employee_email = employee.company_email or employee.personal_email

    hr_emails = get_hr_manager_emails()

    print_format = get_default_print_format(doc.doctype)
    pdf_content = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)

    if doc.workflow_state == "Submitted to Supervisor":
        if not employee.reports_to:
            frappe.log_error(
                "Employee {} has no reports_to set".format(doc.employee),
                "Monthly Reflection - No Supervisor"
            )
            return

        supervisor_contact = get_supervisor_contact(employee)
        supervisor_email = supervisor_contact.email
        supervisor_user = supervisor_contact.user_id

        # Grant supervisor access via User Permission
        add_user_permission(supervisor_user, doc.employee)

        send_email(
            recipients=[supervisor_email],
            subject=frappe._("Monthly Reflection from {}".format(employee.employee_name)),
            message=generate_message(doc, employee.employee_name, supervisor_contact.name, "supervisor"),
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Acknowledged by Supervisor":
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Monthly Reflection has been Acknowledged"),
            message=generate_message(doc, employee.employee_name, None, "employee_acknowledged"),
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Returned by Supervisor":
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Monthly Reflection has been Returned for Revision"),
            message=generate_message(doc, employee.employee_name, None, "employee_rejected"),
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Submitted to HR":
        if hr_emails:
            send_email(
                recipients=hr_emails,
                subject=frappe._("Monthly Reflection from {} - Pending HR Review".format(employee.employee_name)),
                message=generate_message(doc, employee.employee_name, None, "hr_submitted"),
                pdf_content=pdf_content,
                doc_name=doc.name,
            )

    elif doc.workflow_state == "Approved by HR":
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Monthly Reflection has been Approved by HR"),
            message=generate_message(doc, employee.employee_name, None, "employee_hr_approved"),
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Rejected By HR":
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Monthly Reflection has been Returned by HR"),
            message=generate_message(doc, employee.employee_name, None, "employee_hr_rejected"),
            pdf_content=pdf_content,
            doc_name=doc.name,
        )


doc_events = {
    "Monthly Reflection": {
        "on_update": alert,
    }
}
