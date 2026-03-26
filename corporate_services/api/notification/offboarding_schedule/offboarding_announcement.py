import frappe
from frappe.utils import get_fullname, formatdate


@frappe.whitelist()
def get_offboarding_email_preview(docname):
    """Returns rendered subject + HTML body from the Email Template for preview."""
    subject, message = _render_template(docname, frappe.session.user)
    return {"subject": subject, "message": message}


@frappe.whitelist()
def send_offboarding_announcement(docname, recipients=None, send_to_all=0, signature_name=None):
    """Send the offboarding announcement using the ERPNext Email Template."""
    send_to_all = frappe.utils.cint(send_to_all)

    if send_to_all:
        # Fetch all active employees with an email address
        active_employees = frappe.get_all(
            "Employee",
            filters={"status": "Active"},
            fields=["company_email", "personal_email", "employee_name"],
        )
        recipient_list = [
            emp.company_email or emp.personal_email
            for emp in active_employees
            if emp.company_email or emp.personal_email
        ]
        recipient_label = "all active employees"
    else:
        if not recipients:
            frappe.throw("Please provide at least one recipient email address.")
        recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]
        recipient_label = recipients

    if not recipient_list:
        frappe.throw("No valid email addresses found to send the announcement.")

    subject, message = _render_template(docname, frappe.session.user, signature_name)

    frappe.sendmail(
        recipients=recipient_list,
        subject=subject,
        message=message,
        header=("OffBoarding Schedule", "text/html"),
    )

    # Tick farewell_email checkbox and add audit trail comment
    sender_name = get_fullname(frappe.session.user)
    doc = frappe.get_doc("OffBoarding Schedule", docname)

    frappe.db.set_value("OffBoarding Schedule", docname, "farewell_email", 1)
    frappe.db.commit()

    doc.add_comment(
        "Comment",
        f"Offboarding announcement sent to <b>{recipient_label}</b> "
        f"({len(recipient_list)} recipients) by <b>{sender_name}</b>.",
    )

    return f"Announcement sent to {len(recipient_list)} recipient(s) successfully."


def _render_template(docname, user, signature_name=None):
    """
    Fetches the 'Farewell Email Template' and renders it using Jinja
    with context variables matching the template placeholders.
    """
    template = frappe.get_doc("Email Template", "Farewell Email Template")

    doc = frappe.get_doc("OffBoarding Schedule", docname)
    employee = frappe.get_doc("Employee", doc.employee)

    context = {
        "employee_name": employee.employee_name,
        "job_title": employee.designation or "-",
        "company_name": (
            doc.get("company")
            or frappe.defaults.get_user_default("company")
            or ""
        ),
        "last_day_date": (
            formatdate(employee.relieving_date)
            if employee.relieving_date
            else "-"
        ),
        "signature_name": signature_name or get_fullname(user),
    }

    raw_body = template.response_html or template.response or ""
    raw_subject = template.subject or ""

    subject = frappe.render_template(raw_subject, context)
    message = frappe.render_template(raw_body, context)

    return subject, message