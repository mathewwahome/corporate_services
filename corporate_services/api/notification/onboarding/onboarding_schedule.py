import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, get_fullname


def send_30day_onboarding_surveys():
    """
    Runs daily. Finds all employees whose date_of_joining was exactly 30 days ago,
    are Active, and haven't had the survey sent yet (30_day_feedback_survey = 0).
    """
    target_date = add_days(today(), -30)

    employees = frappe.get_all(
        "Employee",
        filters={
            "date_of_joining": target_date,
            "status": "Active",
            "company_email": ["!=", ""],
        },
        fields=["name", "employee_name", "company_email", "company", "date_of_joining"],
    )

    if not employees:
        return

    for emp in employees:
        onboarding_doc = frappe.db.get_value(
            "Onboarding Schedule",
            {"employee": emp.name},
            ["name", "30_day_feedback_survey"],
            as_dict=True
        )

        if not onboarding_doc:
            frappe.logger().warning(
                f"No Onboarding Schedule found for {emp.employee_name} ({emp.name}), skipping."
            )
            continue

        if onboarding_doc.get("30_day_feedback_survey"):
            frappe.logger().info(
                f"30-day survey already sent for {emp.employee_name}, skipping."
            )
            continue

        try:
            send_30day_feedback_survey(
                employee_name=emp.name,
                docname=onboarding_doc.name
            )
            frappe.logger().info(f"30-day survey sent to {emp.employee_name}")

        except Exception:
            frappe.logger().error(
                f"Failed to send 30-day survey to {emp.employee_name}"
            )
            frappe.log_error(
                title=f"30-Day Survey Error: {emp.employee_name}",
                message=frappe.get_traceback()
            )


@frappe.whitelist()
def send_30day_feedback_survey(employee_name, docname=None):
    employee = frappe.get_doc("Employee", employee_name)

    if employee.status != "Active":
        frappe.throw(f"{employee.employee_name} is not an Active employee.")

    if not employee.company_email:
        frappe.throw(f"No company email found for employee {employee.employee_name}.")

    company_name = (
        employee.company
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )

    onboarding_doc_name = docname or frappe.db.get_value(
        "Onboarding Schedule", {"employee": employee_name}, "name"
    )

    base_url = frappe.utils.get_url()
    survey_link = (
        f"{base_url}/app/new-hire-feedback-survey-30-day/new-new-hire-feedback-survey-30-day-1"
        f"?employee={employee_name}"
        f"&employee_name={frappe.utils.quote(employee.employee_name)}"
    )

    email_message = f"""
    <p>Dear {employee.employee_name},</p>

    <p>Congratulations on completing your first 30 days at <strong>{company_name}</strong>!</p>

    <p>We value your feedback and would like to hear about your onboarding experience.
    Your insights will help us improve the onboarding process for future team members.</p>

    <p><strong>Please complete this brief survey:</strong><br>
    <a href="{survey_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px;
    text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
    Take Survey (5 minutes)</a></p>

    <p><strong>Survey Topics:</strong></p>
    <ul>
        <li>Pre-boarding experience</li>
        <li>First day orientation</li>
        <li>Training and resources provided</li>
        <li>Team integration</li>
        <li>Overall satisfaction</li>
    </ul>

    <p>Thank you for your time and feedback!</p>

    <p>Best regards,<br>
    HR Team<br>
    {company_name}</p>
    """

    frappe.sendmail(
        recipients=[employee.company_email],
        subject="Your Feedback Matters - 30-Day Onboarding Survey",
        message=email_message,
    )

    # Tick the checkbox only - no survey doc to link yet since employee creates it themselves
    if onboarding_doc_name:
        frappe.db.set_value(
            "Onboarding Schedule",
            onboarding_doc_name,
            "30_day_feedback_survey",
            1
        )
        frappe.db.commit()

    employee.add_comment("Comment", "30-day feedback survey link sent.")

    return f"30-day feedback survey sent to {employee.employee_name}"


@frappe.whitelist()
def send_welcome_email(docname, email_template, custom_message):
    doc = frappe.get_doc("Onboarding Schedule", docname)
    employee = frappe.get_doc("Employee", doc.employee)

    recipient = employee.company_email or employee.personal_email or doc.employee_email
    if not recipient:
        frappe.throw(_("No email address found for employee {0}.").format(employee.employee_name))

    subject, message = _render_email_template(doc, employee, email_template, custom_message)

    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        now=True,
    )

    frappe.db.set_value("Onboarding Schedule", doc.name, "send_welcome_email", 1)
    frappe.db.commit()

    doc.add_comment(
        "Comment",
        _("Welcome email sent to {0} by {1}.").format(
            recipient, get_fullname(frappe.session.user)
        ),
    )

    return _("Welcome email sent to {0}.").format(employee.employee_name)


@frappe.whitelist()
def send_global_email_invite(docname, email_template, custom_message):
    doc = frappe.get_doc("Onboarding Schedule", docname)
    employee = frappe.get_doc("Employee", doc.employee)

    recipients = _get_global_recipients(employee.name)
    if not recipients:
        frappe.throw(_("No active employee email addresses found."))

    subject, message = _render_email_template(doc, employee, email_template, custom_message)

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        now=True,
    )

    frappe.db.set_value("Onboarding Schedule", doc.name, "send_company_wide_email_intro", 1)
    frappe.db.commit()

    doc.add_comment(
        "Comment",
        _("Global onboarding introduction sent for {0} to {1} recipients by {2}.").format(
            employee.employee_name,
            len(recipients),
            get_fullname(frappe.session.user),
        ),
    )

    return _("Global onboarding introduction sent for {0}.").format(employee.employee_name)


def _render_email_template(doc, employee, email_template, custom_message):
    if not frappe.db.exists("Email Template", email_template):
        frappe.throw(_("Email Template {0} was not found.").format(email_template))

    template = frappe.get_doc("Email Template", email_template)
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")

    context = {
        "doc": doc,
        "employee": employee,
        "employee_name": employee.employee_name,
        "employee_id": employee.name,
        "department": employee.department,
        "designation": employee.designation,
        "company_name": company_name,
        "custom_message": custom_message,
        "signature_name": get_fullname(frappe.session.user),
    }

    raw_subject = template.subject or ""
    raw_body = template.response_html or template.response or ""

    subject = frappe.render_template(raw_subject, context)
    message = frappe.render_template(raw_body, context)
    return subject, message


def _get_global_recipients(exclude_employee=None):
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "company_email", "personal_email"],
    )

    recipients = []
    seen = set()

    for emp in employees:
        if exclude_employee and emp.name == exclude_employee:
            continue

        email = emp.company_email or emp.personal_email
        if email and email not in seen:
            recipients.append(email)
            seen.add(email)

    return recipients
