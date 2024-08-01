import frappe
import csv
import io
from frappe.utils.file_manager import get_file
from datetime import datetime, timedelta

@frappe.whitelist()
def timesheet_import(docname):
    try:
        doc = frappe.get_doc('Timesheet Submission', docname)
        
        file_url = doc.timesheet
        _file = frappe.get_doc("File", {"file_url": file_url})
        file_content = get_file(_file.file_url)[1]
        
        if not file_content:
            frappe.log_error(f"No content retrieved from file: {file_url}", "timesheet_import")
            return "error"
        
        csvfile = io.StringIO(file_content)
        reader = csv.reader(csvfile)
        header = next(reader)

        from_time_tracker = {}
        current_project = None
        timesheet = None

        existing_projects = {p["project_name"]: p["name"] for p in frappe.get_all("Project", fields=["project_name", "name"])}

        for row in reader:
            if not row:
                continue

            if len(row) > 0 and row[0] and row[0] not in ['Projects', 'Meetings', 'Proposals', 'Recurring Tasks', 'Other Tasks/Activities', 'Training/Workshops/Connectathons']:
                if timesheet:
                    try:
                        timesheet.save()
                        frappe.db.commit()
                        frappe.logger().info(f"Saved timesheet for project: {current_project}", "timesheet_import")
                    except Exception as e:
                        error_message = f"Error saving timesheet for project {current_project}: {str(e)}"
                        frappe.log_error(error_message[:140], "timesheet_import")

                current_project = row[0]
                if current_project in existing_projects:
                    try:
                        project_id = existing_projects[current_project]
                        # Create a new Timesheet for the project
                        timesheet = frappe.new_doc("Timesheet")
                        timesheet.employee = doc.employee
                        timesheet.custom_month = doc.month
                        timesheet.parent_project = project_id
                        timesheet.insert()
                        frappe.log_error(f"Started timesheet for project: {current_project} with ID {project_id}", "timesheet_import")
                    except Exception as e:
                        frappe.log_error(f"Error creating timesheet for project {current_project}: {str(e)}", "timesheet_import")
                        current_project = None
                else:
                    frappe.log_error(f"Project {current_project} not found in ERPNext. Skipping...", "timesheet_import")
                    current_project = None
                continue

            if current_project and len(row) > 1:
                task = row[1]

                for idx in range(2, len(header)):
                    if idx >= len(row):
                        continue

                    day_str = header[idx]
                    if row[idx]:
                        try:
                            hours = float(row[idx])
                            day = int(day_str)
                            current_year = datetime.now().year
                            month_name = doc.month
                            month = datetime.strptime(month_name, "%B").month

                            start_of_day = f"{current_year}-{month:02d}-{day:02d} 08:00:00"
                            from_time = datetime.strptime(start_of_day, '%Y-%m-%d %H:%M:%S')

                            if day in from_time_tracker:
                                from_time = from_time_tracker[day] + timedelta(minutes=1)

                            to_time = from_time + timedelta(hours=hours)

                            if is_time_overlap(doc.employee, from_time, to_time):
                                frappe.log_error(f"Time entry overlaps with existing timesheet entries: {from_time} - {to_time}", "timesheet_import")
                                continue

                            try:
                                timesheet_detail = frappe.new_doc("Timesheet Detail")
                                timesheet_detail.parent = timesheet.name
                                timesheet_detail.parenttype = timesheet.doctype
                                timesheet_detail.parentfield = "time_logs"
                                timesheet_detail.activity_type = "Projects"
                                timesheet_detail.hours = hours
                                timesheet_detail.custom_date = day
                                timesheet_detail.from_time = from_time
                                timesheet_detail.to_time = to_time
                                timesheet_detail.project = project_id
                                timesheet_detail.custom_tasks = task

                                timesheet.append("time_logs", timesheet_detail)
                                frappe.logger().info(f"Created timesheet detail entry: Project: {current_project}, Task: {task}, Hours: {hours}", "timesheet_import")
                            except Exception as e:
                                error_message = f"Error creating timesheet detail entry: {str(e)}"
                                frappe.log_error(error_message[:140], "timesheet_import")

                            from_time_tracker[day] = to_time
                        except ValueError as e:
                            frappe.log_error(f"Invalid value in row: {row[idx]} - {e}", "timesheet_import")

        if timesheet:
            try:
                timesheet.save()
                frappe.db.commit()
                frappe.logger().info(f"Saved timesheet for project: {current_project}", "timesheet_import")
            except Exception as e:
                error_message = f"Error saving timesheet for project {current_project}: {str(e)}"
                frappe.log_error(error_message[:140], "timesheet_import")

        return "success"
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_import")
        return "error"

def is_time_overlap(employee, from_time, to_time):
    """ Check if the time entry overlaps with existing entries for the employee """
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
