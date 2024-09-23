import frappe
from frappe.utils import getdate, add_months
from datetime import timedelta

def update_annual_leave_allocations():
    leave_type = "Annual Leave"
    leave_days = 2

    today = getdate()
    start_date = today.replace(day=1)
    end_date = add_months(start_date, 1) - timedelta(days=1)

    employees = frappe.get_all("Employee", fields=["name"])

    for employee in employees:
        allocation = frappe.get_all("Leave Allocation", filters={
            "employee": employee["name"],
            "leave_type": leave_type,
            "from_date": ["between", [start_date, end_date]],
            "to_date": ["between", [start_date, end_date]]
        }, fields=["name"])

        if allocation:
            allocation_doc = frappe.get_doc("Leave Allocation", allocation[0]["name"])
            allocation_doc.new_leaves_allocated += leave_days
            allocation_doc.total_leaves_allocated += leave_days
            allocation_doc.save(ignore_permissions=True)
        else:
            leave_allocation = frappe.get_doc({
                "doctype": "Leave Allocation",
                "employee": employee["name"],
                "leave_type": leave_type,
                "from_date": start_date,
                "to_date": end_date,
                "new_leaves_allocated": leave_days,
                "total_leaves_allocated": leave_days
            })
            leave_allocation.insert(ignore_permissions=True)

    frappe.db.commit()
