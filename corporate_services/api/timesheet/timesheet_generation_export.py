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

        start_date = datetime(previous_year, previous_month, 28).date()
        end_date = datetime(current_year, current_month, 28).date()   
        
        dates = []
        while start_date <= end_date:
            dates.append(start_date.strftime('%d'))
            start_date += timedelta(days=1)

        #get the user linked to the specific employee
        user =  frappe.db.get_value('User', employee, 'user')
        # get the projects allocated to the specific employee
        projects = frappe.db.get_value('Project', user, 'project_name')
        
             
        data = [
            ["Projects", "Tasks"] + dates,
            [projects],
            ["Meetings"],
            ["Proposals"],
            ["Recurring Tasks"],
            ["Other Tasks/Activities (Activities that are not project-specific but are essential to running the company)"],
            ["Training/Workshops/Connectathons"]

        ]

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
