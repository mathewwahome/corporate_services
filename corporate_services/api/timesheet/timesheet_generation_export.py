import frappe
import csv
from io import StringIO
from frappe.utils.file_manager import save_file
from datetime import timedelta

@frappe.whitelist()
def timesheet_generation_export(docname):
    try:
        doc = frappe.get_doc('Timesheet Submission', docname)
        
        employee = doc.employee
        start_date = doc.start_date
        end_date = doc.end_date
        month = doc.month
        employee_name = frappe.db.get_value('Employee', employee, 'employee_name')
        
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%d'))
            current_date += timedelta(days=1)

        data = [
            ["Actvity Type", "Tasks"] + dates,
            ["Project"],
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
        file_name = f"{employee_name}_{month}_{docname}.xlsx" # csv

        file_url = save_file(file_name, csv_content, "Timesheet Submission", docname, is_private=0)

        return file_url

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_generation_export")
        return "error"
