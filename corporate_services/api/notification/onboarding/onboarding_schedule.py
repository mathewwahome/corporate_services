import frappe
from frappe.email.doctype.email_template.email_template import get_email_template
from frappe.utils import validate_email_address

@frappe.whitelist()
def send_welcome_email(docname, email_template, custom_message):
    doc = frappe.get_doc("Onboarding Schedule", docname)
    
    emp_info = frappe.db.get_value("Employee", doc.employee, ["company"], as_dict=True) or {}
    
    doc.company = emp_info.get("company") or "IntelliSOFT Consulting Limited"

    result = get_email_template(email_template, {"doc": doc, "custom_message": custom_message})
    
    frappe.sendmail(
        recipients=[doc.employee_email],
        subject=result.get("subject"),
        message=result.get("message"),
        reference_doctype="Onboarding Schedule",
        reference_name=docname
    )

    doc.db_set("send_welcome_email", 1)
    return "Single Welcome Email Sent"

@frappe.whitelist()
def send_global_email_invite(docname, email_template, custom_message):
    frappe.enqueue(
        method=_send_global_email_background,
        queue="long",
        docname=docname,
        email_template=email_template,
        custom_message=custom_message
    )
    return "Global Emails Queued"

def _send_global_email_background(docname, email_template, custom_message):
    doc = frappe.get_doc("Onboarding Schedule", docname)
    
    new_hire = frappe.get_doc("Employee", doc.employee)
    company_name = new_hire.company or "IntelliSOFT Consulting Limited"

    recipients = frappe.get_all("Employee", filters={"status": "Active"}, fields=["prefered_email", "company_email"])

    for emp in recipients:
        email_addr = emp.company_email or emp.prefered_email
        if not email_addr or not validate_email_address(email_addr):
            continue

        context = {
            "employee": {
                "employee_name": new_hire.employee_name,
                "designation": new_hire.designation,
                "department": new_hire.department,
                "company_email": new_hire.company_email or new_hire.prefered_email,
                "salutation": new_hire.salutation,
            },
            "company_name": company_name,
            "custom_message": custom_message
        }

        result = get_email_template(email_template, context)

        frappe.sendmail(
            recipients=[email_addr],
            subject=result.get("subject"),
            message=result.get("message")
        )

    doc.db_set("send_company_wide_email_intro", 1)
    frappe.db.commit()