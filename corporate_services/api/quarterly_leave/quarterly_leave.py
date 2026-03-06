import frappe
from frappe.utils import nowdate, getdate


@frappe.whitelist()
def send_quarterly_notifications(manual=False):

    doc = frappe.get_single("Quarterly Leave Notification")

    if not doc.enabled and not manual:
        return

    today = getdate(nowdate())
    current_year = today.year

    month_map = {
        "January": 1, "February": 2, "March": 3,
        "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9,
        "October": 10, "November": 11, "December": 12
    }

    for row in doc.quarterly_leave:

        end_month = month_map.get(row.end_month)

        should_send = (
            manual or
            (
                today.month == end_month
                and today.day == row.notification_day
                and row.last_sent_year != current_year
            )
        )

        if not should_send:
            continue

        employees = frappe.get_all(
            "Employee",
            filters={
                "status": "Active",
                "company": doc.company
            },
            fields=["name", "employee_name", "company_email"]
        )

        for emp in employees:

            balance = frappe.db.get_value(
                "Leave Allocation",
                {
                    "employee": emp.name,
                    "leave_type": doc.leave_type,
                    "docstatus": 1
                },
                "remaining_leaves"
            ) or 0

            if not emp.company_email:
                continue

            frappe.sendmail(
                recipients=[emp.company_email],
                subject=f"{row.quarter_name} {current_year} Leave Balance Update",
                message=f"""
                <p>Hi {emp.employee_name},</p>
                <p>This is your {row.quarter_name} {current_year} leave balance update.</p>
                <p>Your remaining leave balance is <b>{balance}</b> days.</p>
                """
            )

        row.last_sent_year = current_year

    doc.save()