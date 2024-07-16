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
        month_name = doc.month
        
        current_year = datetime.now().year
        current_month = datetime.strptime(month_name, "%B").month

        if current_month == 1:
            previous_year = current_year - 1
            previous_month = 12
        else:
            previous_year = current_year
            previous_month = current_month - 1

        start_date = datetime(previous_year, previous_month, 29).date()
        end_date = datetime(current_year, current_month, 28).date()   
        
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
                    if projects_list:
                        frappe.log_error(f"Projects found for User ID {user_id}: {projects_list}")

        header = ["Projects", "Tasks"] + dates
        
        additional_rows = [
            ["Meetings"],
            [],
            ["Proposals"],
            [],
            ["Recurring Tasks"],
            [],
            ["Other Tasks/Activities (Activities that are not project-specific but are essential to running the company)"],
            [],
            ["Training/Workshops/Connectathons"]

        ]
        data = [header] + projects_list + additional_rows

        output = StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerows(data)

        csv_content = output.getvalue().encode('utf-8')
        file_name = f"{employee_name}_{current_month}_{docname}.csv"

        file_url = save_file(file_name, csv_content, "Timesheet Submission", docname, is_private=0)

        return file_url

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_generation_export")
        return "error"
