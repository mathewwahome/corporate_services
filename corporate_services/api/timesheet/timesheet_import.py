import frappe
import csv
import io
from frappe.utils.file_manager import get_file

@frappe.whitelist()
def timesheet_import(docname):
    try:
        doc = frappe.get_doc('Timesheet Submission', docname)
        
        file_url = doc.timesheet

        _file = frappe.get_doc("File", {"file_url": file_url})
        file_content = get_file(_file.file_url)[1]
        
        csvfile = io.StringIO(file_content)
        reader = csv.reader(csvfile)
        header = next(reader)

        timesheet = frappe.new_doc("Timesheet")
        timesheet.employee = doc.employee
        timesheet.custom_month = doc.month
        timesheet.insert()
        
        activity_type = "Projects"
        project = None
        
        for row in reader:
            if not row:
                continue

            if len(row) < 2:
                frappe.log_error(f"Row has insufficient columns: {row}", "timesheet_import")
                continue

            if row[0] in ['Projects', 'Meetings', 'Proposals', 'Recurring Tasks', 'Other Tasks/Activities', 'Training/Workshops/Connectathons']:
                activity_type = row[0]
                project = None
                continue

            if activity_type == "Projects":
                project = row[0]
            task = row[1]

            if not task or task in ['Projects', 'Tasks']:
                continue

            for idx in range(2, len(header)):
                if idx >= len(row):
                    continue

                date_str = header[idx]

                if row[idx]:
                    try:
                        hours = float(row[idx])
                        date = int(date_str)
                        
                        create_timesheet_detail_entry(timesheet, activity_type, task, date, hours, project)
                    except ValueError:
                        pass

        frappe.db.commit()
        return "success"
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_import")
        return "error"

def create_timesheet_detail_entry(timesheet, activity_type, task, date, hours, project):
    timesheet_detail = frappe.new_doc("Timesheet Detail")
    
    timesheet_detail.parent = timesheet.name
    timesheet_detail.parenttype = timesheet.doctype
    timesheet_detail.parentfield = "time_logs"
    
    timesheet_detail.activity_type = activity_type
    timesheet_detail.hours = hours
    timesheet_detail.custom_date = date
    
    if project:
        timesheet_detail.project = project

    if activity_type == "Projects":
        timesheet_detail.custom_tasks = task
    elif activity_type == "Meetings":
        timesheet_detail.custom_meetings = task
    elif activity_type == "Training/Workshops/Connectathons":
        timesheet_detail.custom_trainingworkshopsconnectathons = task
    elif activity_type == "Proposals":
        timesheet_detail.custom_proposals = task
    elif activity_type == "Recurring Tasks":
        timesheet_detail.custom_recurring_tasks = task
    elif activity_type == "Other Tasks/Activities":
        timesheet_detail.custom_other_tasksactivities = task

    timesheet.append("time_logs", timesheet_detail)
    timesheet.save()
