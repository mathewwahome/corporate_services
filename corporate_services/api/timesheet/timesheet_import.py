import frappe
import csv
import io
import os
import tempfile
from frappe.utils.file_manager import get_file
from datetime import datetime, timedelta
from frappe import _
import openpyxl

def calculate_total_hours(project_timesheets, activity_timesheets):
    total_hours = 0
    for timesheet in list(project_timesheets.values()) + list(activity_timesheets.values()):
        for time_log in timesheet.time_logs:
            total_hours += time_log.hours
    return total_hours

@frappe.whitelist()
@frappe.whitelist()
def timesheet_import(docname):
    """Imports timesheet data from a file."""
    try:
        doc = frappe.get_doc('Timesheet Submission', docname)
        employee = doc.employee
        
        file_url = doc.timesheet
        _file = frappe.get_doc("File", {"file_url": file_url})
        
        if _file.file_url:
            file_content = get_file(_file.file_url)[1]
        else:
            frappe.throw(_("File URL is missing. Please upload the file again."))
        
        if not file_content:
            frappe.log_error(f"No content retrieved from file: {file_url}", "timesheet_import")
            return "error"
        
        file_extension = _file.file_name.split('.')[-1].lower()
        data = None
        if file_extension == 'csv':
            csvfile = io.StringIO(file_content.decode('utf-8'))
            reader = csv.reader(csvfile)
            data = list(reader)
        elif file_extension in ['xls', 'xlsx']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                workbook = openpyxl.load_workbook(temp_file_path, data_only=True)
                sheet = workbook.active
                data = [[cell.value for cell in row] for row in sheet.iter_rows()]
            finally:
                os.unlink(temp_file_path) 
        else:
            frappe.throw(_("Unsupported file format. Please upload a CSV or Excel file."))
        
        if not data:
            frappe.throw(_("No data found in the uploaded file."))

        header = data[0]

        existing_projects = {p["project_name"]: p["name"] for p in frappe.get_all("Project", fields=["project_name", "name"])}
        activity_types = frappe.get_all('Activity Type', fields=['name'])

        from_time_tracker = {}
        project_timesheets = {}
        activity_timesheets = {}
        non_empty_activities = set()

        activity_field_mapping = {
            "Meetings": "custom_meetings",
            "Training/Workshops/Connectathons": "custom_trainingworkshopsconnectathons",
            "Proposals": "custom_proposals",
            "Recurring Tasks": "custom_recurring_tasks",
            "Other Tasks/Activities": "custom_other_tasksactivities"
        }

        for activity_type in activity_types:
            if activity_type['name'] not in activity_field_mapping:
                activity_field_mapping[activity_type['name']] = None

        minimum_hours = frappe.db.get_value('Employee', employee, 'custom_hrs_per_month')
        
        # First pass to determine non-empty activities
        for row in data[1:]:  # Skip header
            if not row or len(row) < 2:
                continue

            activity_type = row[0]
            if activity_type in [activity['name'] for activity in activity_types]:
                current_activity = activity_type
                current_project = None
                continue
            elif activity_type in existing_projects:
                current_project = activity_type
                current_activity = "Projects"
                continue

            if any(cell and float(cell) > 0 for cell in row[2:]):
                if current_project:
                    non_empty_activities.add(("project", current_project))
                else:
                    non_empty_activities.add(("activity", current_activity))

        # Second pass to process data
        for row in data[1:]:  # Skip header
            if not row or len(row) < 2:
                continue

            activity_type = row[0]
            if activity_type in [activity['name'] for activity in activity_types]:
                current_activity = activity_type
                current_project = None
                continue
            elif activity_type in existing_projects:
                current_project = activity_type
                current_activity = "Projects"
                continue

            if current_project and ("project", current_project) not in non_empty_activities:
                continue
            if not current_project and ("activity", current_activity) not in non_empty_activities:
                continue

            task = row[1]

            if current_project:
                project_name = existing_projects[current_project]
                if project_name not in project_timesheets:
                    project_timesheets[project_name] = create_timesheet(doc, project=project_name, month_name=doc.month_year)
                target_timesheet = project_timesheets[project_name]
            else:
                if current_activity not in activity_timesheets:
                    activity_timesheets[current_activity] = create_timesheet(doc, activity_type=current_activity, month_name=doc.month_year)
                target_timesheet = activity_timesheets[current_activity]

            if len(row) > 1:
                for idx in range(2, len(header)):
                    if idx >= len(row) or not row[idx]:
                        continue

                    day_str = header[idx]
                    try:
                        hours = float(row[idx])
                        if hours == 0:
                            continue

                        day = int(day_str)
                        date_str = doc.month_year
                        month = int(date_str.split('-')[0])
                        year = int(date_str.split('-')[1])
                        month_name = datetime(year, month, 1).strftime('%B')
                        month = datetime.strptime(month_name, "%B").month

                        start_of_day = f"{year}-{month:02d}-{day:02d} 08:00:00"
                        from_time = datetime.strptime(start_of_day, '%Y-%m-%d %H:%M:%S')

                        if day in from_time_tracker:
                            from_time = from_time_tracker[day] + timedelta(minutes=1)

                        to_time = from_time + timedelta(hours=hours)

                        if is_time_overlap(doc.employee, from_time, to_time):
                            frappe.log_error(f"Time entry overlaps with existing timesheet entries: {from_time} - {to_time}", "timesheet_import")
                            continue

                        create_timesheet_detail_entry(target_timesheet, from_time, to_time, current_activity, task, day, hours, current_project, activity_field_mapping)
                        from_time_tracker[day] = to_time
                       
                    except ValueError as e:
                        frappe.log_error(f"Invalid value in row: {row[idx]} - {e}", "timesheet_import")

        total_hours = calculate_total_hours(project_timesheets, activity_timesheets)

        if total_hours < minimum_hours:
            frappe.log_error(f"Total hours ({total_hours}) are less than {minimum_hours}. Timesheet not uploaded.", "timesheet_import")
            return "error: Total hours are less than {}".format(minimum_hours)

        if total_hours >= minimum_hours:
            save_timesheets(project_timesheets)
            save_timesheets(activity_timesheets)
            
            return "success"
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_import")
        return "error"

def create_timesheet(doc, project=None, activity_type=None, month_name=None, total_hours=0):
    timesheet = frappe.new_doc("Timesheet")
    timesheet.employee = doc.employee
    timesheet.custom_month = month_name
    timesheet.total_working_hours = total_hours
    
    if project:
        timesheet.parent_project = project
        timesheet.custom_timesheet_type = "Project Based"
    if activity_type:
        timesheet.custom_activity_type = activity_type
        timesheet.custom_timesheet_type = "Other Activities"
    
    return timesheet

def save_timesheets(timesheets):
    for timesheet in timesheets.values():
        try:
            if timesheet.time_logs:
                timesheet.insert()
                timesheet.save()
                frappe.db.commit()
            else:
                frappe.log_error(f"Timesheet for {timesheet.employee} has no time logs. Skipping.", "timesheet_import")
        except Exception as e:
            frappe.log_error(f"Error saving timesheet: {str(e)}", "timesheet_import")

def is_time_overlap(employee, from_time, to_time):
    """Check if the time entry overlaps with existing entries for the employee."""
    submissions = frappe.get_all("Timesheet Submission", filters={"employee": employee}, fields=["name"])
    
    for submission in submissions:
        details = frappe.get_all("Timesheet Detail",
            filters={"parent": submission.name,
                     "from_time": ["<=", to_time],
                     "to_time": [">=", from_time]},
            fields=["from_time", "to_time"]
        )
        
        for entry in details:
            if not (to_time <= entry["from_time"] or from_time >= entry["to_time"]):
                return True

    return False

def create_timesheet_detail_entry(timesheet, from_time, to_time, activity_type, task, day, hours, project=None, activity_field_mapping=None):
    try:
        timesheet_detail = {
            "activity_type": activity_type,
            "hours": hours,
            "custom_date": day,
            "from_time": from_time,
            "to_time": to_time,
            "is_billable": 1,
        }
        
        if project:
            existing_projects = {p["project_name"]: p["name"] for p in frappe.get_all("Project", fields=["project_name", "name"])}
            project_id = existing_projects.get(project)
            timesheet_detail["project"] = project_id
            timesheet_detail["custom_tasks"] = task
        else:
            field_name = activity_field_mapping.get(activity_type, None)
            if field_name:
                timesheet_detail[field_name] = hours
                timesheet_detail["custom_tasks"] = task
        
        timesheet.append("time_logs", timesheet_detail)
        
    except Exception as e:
        frappe.log_error(f"Error creating timesheet detail entry: {str(e)}", "timesheet_import")
