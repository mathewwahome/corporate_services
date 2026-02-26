import frappe
from frappe.utils import today, add_days, getdate


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

    # Tick the checkbox only — no survey doc to link yet since employee creates it themselves
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