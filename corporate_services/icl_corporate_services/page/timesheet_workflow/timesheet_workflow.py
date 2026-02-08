import frappe

@frappe.whitelist()
def say_hello():
    """Simple hello function"""
    return {"message": "Hello from the backend!"}


@frappe.whitelist()
def get_current_employee():
    user = frappe.session.user

    # Try to get linked Employee
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["name", "employee_name"],
        as_dict=True
    )

    if employee:
        return employee

    # Fallback: get the User's full name
    full_name = frappe.db.get_value("User", user, "full_name")
    return {"name": user, "employee_name": full_name or user}


@frappe.whitelist()
def get_all_employees():
    """
    Returns a list of all employees with their name, employee_name, department, and designation
    """
    employees = frappe.get_all(
        "Employee",
        fields=["name", "employee_name", "department", "designation"]
    )
    return employees




@frappe.whitelist()
def get_employee_timesheets(employee_name):
    timesheet_details = frappe.get_all(
        'Timesheet Detail',
        filters={'employee': employee_name},
        fields=['task', 'hours'], 
        order_by='date desc'
    )
    return timesheet_details


@frappe.whitelist()
def get_timesheet_submissions_by_employee(employee_name):
    """
    Returns Timesheet Submissions for a specific employee.
    """
    return frappe.get_all(
        "Timesheet Submission",
        filters={"employee_name": employee_name},
        fields=["name", "month_year", "total_working_hours", "status", "creation"],
        order_by="creation desc"
    )


@frappe.whitelist()
def get_all_timesheet_submissions():
    """
    Returns all Timesheet Submission documents.
    """
    timesheets = frappe.get_all(
        "Timesheet Submission",
        fields=[
            "name",
            "employee",
            "employee_name",
            "month_year",
            "total_working_hours",
            "status",
            "creation"
        ],
        order_by="creation desc"
    )
    return timesheets
