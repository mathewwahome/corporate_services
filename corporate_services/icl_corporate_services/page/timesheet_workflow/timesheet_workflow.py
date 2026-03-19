import frappe

from frappe import _
from frappe.utils import today, get_first_day, get_last_day, add_months

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


@frappe.whitelist()
def get_timesheet_submission_details(submission_name):
    """
    Get detailed breakdown of a specific timesheet submission
    including all related timesheets, projects, and tasks by fetching linked Timesheet documents
    """
    # Get the submission document with child table
    submission = frappe.get_doc("Timesheet Submission", submission_name)
    
    # Check if timesheet_per_project exists and has data
    if not hasattr(submission, 'timesheet_per_project') or not submission.timesheet_per_project:
        return {
            "submission": {
                "name": submission.name,
                "employee": submission.employee,
                "employee_name": submission.employee_name,
                "month_year": submission.month_year,
                "total_working_hours": submission.total_working_hours or 0,
                "status": submission.status,
                "creation": submission.creation
            },
            "projects": [],
            "tasks": [],
            "timesheets": [],
            "total_entries": 0
        }
    
    # Get all timesheet details by fetching linked Timesheet documents
    timesheets = []
    projects = {}
    tasks = {}
    
    timesheet_names = set()
    for row in submission.timesheet_per_project:
        if row.get("timesheet"):
            timesheet_names.add(row.get("timesheet"))
    
    # Fetch each Timesheet document and extract time_logs
    for timesheet_name in timesheet_names:
        try:
            timesheet_doc = frappe.get_doc("Timesheet", timesheet_name)
            
            if hasattr(timesheet_doc, 'time_logs') and timesheet_doc.time_logs:
                for time_log in timesheet_doc.time_logs:
                    ts_entry = {
                        "parent": timesheet_name,
                        "date": time_log.get("custom_date"),
                        "hours": time_log.get("hours") or 0,
                        "activity_type": time_log.get("activity_type"),
                        "project": time_log.get("project"),
                        "task": time_log.get("custom_tasks"),
                    }
                    timesheets.append(ts_entry)
                    
                    # Group by project
                    project = time_log.get("project") or "No Project"
                    if project not in projects:
                        projects[project] = {
                            "project": project,
                            "hours": 0,
                            "tasks": set(),
                            "entries": 0
                        }
                    projects[project]["hours"] += (time_log.get("hours") or 0)
                    if time_log.get("custom_tasks"):
                        projects[project]["tasks"].add(time_log.get("custom_tasks"))
                    projects[project]["entries"] += 1
                    
                    # Group by task
                    task = time_log.get("custom_tasks") or "No Task"
                    task_key = f"{task}|{project}"
                    if task_key not in tasks:
                        tasks[task_key] = {
                            "task": task,
                            "project": project,
                            "hours": 0,
                            "entries": 0
                        }
                    tasks[task_key]["hours"] += (time_log.get("hours") or 0)
                    tasks[task_key]["entries"] += 1
        except Exception as e:
            frappe.log_error(f"Error fetching timesheet {timesheet_name}: {str(e)}")
            continue
    
    project_list = [
        {
            "project": k,
            "hours": v["hours"],
            "task_count": len(v["tasks"]),
            "entries": v["entries"]
        }
        for k, v in projects.items()
    ]
    project_list.sort(key=lambda x: x["hours"], reverse=True)
    
    task_list = sorted(tasks.values(), key=lambda x: x["hours"], reverse=True)
    
    return {
        "submission": {
            "name": submission.name,
            "employee": submission.employee,
            "employee_name": submission.employee_name,
            "month_year": submission.month_year,
            "total_working_hours": submission.total_working_hours or 0,
            "status": submission.status,
            "creation": submission.creation
        },
        "projects": project_list,
        "tasks": task_list,
        "timesheets": timesheets,
        "total_entries": len(timesheets)
    }
    
@frappe.whitelist()
def create_salary_slip_from_timesheet(submission_name, employee):
    """
    Prepare data for creating a Salary Slip from a Timesheet Submission
    """
    try:
        submission = frappe.get_doc("Timesheet Submission", submission_name)
        
        if submission.status != "Approved":
            frappe.throw(_("Only approved timesheet submissions can be used to create salary slips"))
        
        existing_slip = frappe.db.exists("Salary Slip", {
            "custom_timesheet_submission": submission_name,
            "docstatus": ["<", 2]
        })
        
        if existing_slip:
            frappe.throw(_("A Salary Slip already exists for this timesheet submission: {0}").format(existing_slip))
        
        employee_doc = frappe.get_doc("Employee", employee)
        
        # Parse month_year to get start and end date
        try:
            from dateutil import parser
            month_date = parser.parse(submission.month_year)
            start_date = get_first_day(month_date)
            end_date = get_last_day(month_date)
        except:
            start_date = get_first_day(today())
            end_date = get_last_day(today())
        
        # Return data to pre-fill the form
        return {
            "employee": employee,
            "employee_name": employee_doc.employee_name,
            "company": employee_doc.company,
            "posting_date": today(),
            "start_date": start_date,
            "end_date": end_date,
            "salary_slip_based_on_timesheet": 1,
            "custom_timesheet_submission": submission_name,
            "custom_total_working_hours": submission.total_working_hours,
            "custom_month_year": submission.month_year
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Prepare Salary Slip Data Error"))
        frappe.throw(_("Error: {0}").format(str(e)))