import frappe
from frappe.utils import get_url_to_form


def get_default_print_format(doctype):
    return (
        frappe.db.get_value(
            "Property Setter",
            {"doc_type": doctype, "property": "default_print_format"},
            "value",
        )
        or frappe.db.get_value(
            "Print Format",
            {"doc_type": doctype},
            "name",
        )
        or "Standard"
    )

def send_email(recipients, subject, message, pdf_content, doc_name):
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=[{
            'fname': '{}.pdf'.format(doc_name),
            'fcontent': pdf_content
        }],
        header=("Exit Interview", "text/html")
    )


def generate_message(doc, employee_name, email_type):
    doctype_url = get_url_to_form(doc.doctype, doc.name)
    messages = {
        # Employee submits → Supervisor receives
        "supervisor": """
            Dear {},<br><br>
            {} has submitted an {} for your review and approval.
            You can view it <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            {}
        """.format(doc.custom_supervisor_name or "Supervisor", employee_name, doc.doctype, doctype_url, employee_name),

        # Supervisor approves → HR receives
        "hr": """
            Dear HR Manager,<br><br>
            You have a new {} for <b>{}</b>, approved by the Supervisor and submitted for your
            final review. You can view it <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            {}
        """.format(doc.doctype, employee_name, doctype_url, employee_name),

        # Supervisor rejects → Employee receives
        "employee_rejected_supervisor": """
            Dear {},<br><br>
            Your {} has been reviewed and unfortunately rejected by your Supervisor.
            You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            Supervisor
        """.format(employee_name, doc.doctype, doctype_url),

        # HR rejects → Employee receives
        "employee_rejected_hr": """
            Dear {},<br><br>
            Your {} has been reviewed and unfortunately rejected by the HR Department.
            You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            HR Department
        """.format(employee_name, doc.doctype, doctype_url),

        # HR approves → Employee receives
        "employee_approved_hr": """
            Dear {},<br><br>
            Your {} has been reviewed and approved by the HR Department.
            You can view the details <a href="{}">here</a>.<br><br>
            Kind regards,<br>
            HR Department
        """.format(employee_name, doc.doctype, doctype_url),
    }

    return messages[email_type]


def alert(doc, method):
    if doc.workflow_state not in [
        "Submitted to Supervisor",
        "Rejected By Supervisor",
        "Submitted to HR",
        "Rejected By HR",
        "Approved by HR",
    ]:
        return

    employee = frappe.get_doc("Employee", doc.employee)
    employee_email = employee.company_email or employee.personal_email

    print_format = get_default_print_format(doc.doctype)
    pdf_content = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)

    if doc.workflow_state == "Submitted to Supervisor":
        if not employee.reports_to:
            return
        supervisor = frappe.get_doc("Employee", employee.reports_to)
        supervisor_email = supervisor.company_email or supervisor.personal_email

        message = generate_message(doc, employee.employee_name, "supervisor")
        send_email(
            recipients=[supervisor_email],
            subject=frappe._("Exit Interview Submitted – {}".format(employee.employee_name)),
            message=message,
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Rejected By Supervisor":
        message = generate_message(doc, employee.employee_name, "employee_rejected_supervisor")
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Exit Interview has been Rejected by Supervisor"),
            message=message,
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Submitted to HR":
        hr_managers = frappe.get_all("Has Role", filters={"role": "HR Manager"}, fields=["parent"])
        hr_manager_emails = [
            frappe.get_value("User", hm.parent, "email")
            for hm in hr_managers
            if frappe.get_value("User", hm.parent, "email")
        ]

        message = generate_message(doc, employee.employee_name, "hr")
        send_email(
            recipients=hr_manager_emails,
            subject=frappe._("Exit Interview Submitted to HR – {}".format(employee.employee_name)),
            message=message,
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

        # Tick the exit interview checkbox and set the link on the employee's OffBoarding Schedule
        offboarding = frappe.db.get_value(
            "OffBoarding Schedule",
            {"employee": doc.employee},
            "name"
        )
        if offboarding:
            frappe.db.set_value(
                "OffBoarding Schedule",
                offboarding,
                {
                    "exit_interview_with_supervisor": 1,
                    "exit_interview_link": doc.name,
                }
            )
            frappe.db.commit()

    elif doc.workflow_state == "Rejected By HR":
        message = generate_message(doc, employee.employee_name, "employee_rejected_hr")
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Exit Interview has been Rejected by HR"),
            message=message,
            pdf_content=pdf_content,
            doc_name=doc.name,
        )

    elif doc.workflow_state == "Approved by HR":
        message = generate_message(doc, employee.employee_name, "employee_approved_hr")
        send_email(
            recipients=[employee_email],
            subject=frappe._("Your Exit Interview has been Approved by HR"),
            message=message,
            pdf_content=pdf_content,
            doc_name=doc.name,
        )


doc_events = {
    "Exit Interview": {
        "on_update": alert
    }
}