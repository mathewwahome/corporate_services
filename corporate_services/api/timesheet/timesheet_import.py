import frappe
import csv
import io
from frappe.utils.file_manager import get_file
from datetime import datetime

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
        timesheet.start_date = doc.start_date
        timesheet.end_date = doc.end_date
        timesheet.insert()

        current_activity_type = None
        # project = None
        
        for row in reader:
            task_name = row[1]
            activity_type = row[0]
            project = row[0]

            if activity_type:
                
                if activity_type in ['Projects','Meetings', 'Proposals', 'Recurring Tasks', 'Other Tasks/Activities', 'Training/Workshops/Connectathons']: 
                    # latter on create the fonction that will pull the activity_types from the Doctype Activity Type - mathew
                    current_activity_type = activity_type
                if activity_type == 'Projects':
                    project = row[0]
            
            if not task_name or task_name in ['Actvity Type', 'Tasks']:
                continue

            for idx in range(2, len(header)):
                date_str = header[idx]

                if row[idx]:
                    try:
                        hours = float(row[idx])
                        date = int(date_str)
                        
                        # day_number = int(date_str)
                        # if doc.start_date:
                        #     date = doc.start_date.replace(day=day_number)
                        # elif doc.end_date:
                        #     date = doc.end_date.replace(day=day_number)
                        # else:
                        #     date = int(date_str)

                        
                        
                        create_timesheet_detail_entry(timesheet, current_activity_type, task_name, date, hours, project)
                    except ValueError:
                        pass

        frappe.db.commit()
        return "success"
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_import")
        return "error"

def create_timesheet_detail_entry(timesheet, activity_type, task_name, date, hours, project):
    timesheet_detail = frappe.new_doc("Timesheet Detail")
    
    timesheet_detail.parent = timesheet.name
    timesheet_detail.parenttype = timesheet.doctype
    timesheet_detail.parentfield = "time_logs"
    
    timesheet_detail.activity_type = activity_type
    timesheet_detail.hours = hours
    timesheet_detail.custom_date = date
    timesheet_detail.custom_tasks = task_name
    
    if project:
        timesheet_detail.project = project
        
    timesheet.append("time_logs", timesheet_detail)
    timesheet.save()
