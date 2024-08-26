import frappe
import csv
from io import StringIO
from frappe.utils.file_manager import save_file
from datetime import datetime, timedelta

@frappe.whitelist()
def timesheet_generation_export(docname):
    try:
        doc = frappe.get_doc('Timesheet Submission', docname)
        
        employee = doc.employee
        employee_name = frappe.db.get_value('Employee', employee, 'employee_name')
        
        date_str = doc.month_year
        
        month = int(date_str.split('-')[0])
        year = int(date_str.split('-')[1])
        
        month_name = datetime(year, month, 1).strftime('%B')

        if month == 1:
            previous_year = year - 1
            previous_month = 12
        else:
            previous_year = year
            previous_month = month - 1

        start_date = datetime(previous_year, previous_month, 29).date()
        end_date = datetime(year, month, 28).date()   
        
        dates = []
        while start_date <= end_date:
            dates.append(start_date.strftime('%d'))
            start_date += timedelta(days=1)
        
        
        user_id = frappe.db.get_value('Employee', employee, 'user_id')
        projects_list = []
        
        if user_id:
            projects = frappe.get_all('Project', fields=['name', 'project_name'])
            if projects:
                for project in projects:
                    projects_user = frappe.get_all('Project User', filters={'parent': project['name'], 'user': user_id})
                    if projects_user:
                        projects_list.append([project['project_name']])
                        projects_list.append([])
                        projects_list.append([])

        header = ["Projects", "Tasks"] + dates
        
        activity_types = frappe.get_all('Activity Type', fields=['name'])
        additional_rows = []
        for activity in activity_types:
            additional_rows.append([activity['name']])
            additional_rows.append([])
        
        
       
        data = [header] + projects_list + additional_rows

        output = StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerows(data)

        csv_content = output.getvalue().encode('utf-8')

        file_name = f"{employee_name}-{month_name}{year}-Timesheet-.xlsx"


        file_url = save_file(file_name, csv_content, "Timesheet Submission", docname, is_private=0)

        return file_url

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_generation_export")
        return "error"