import frappe
from frappe.utils.file_manager import save_file
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from io import BytesIO

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
        
        days = []
        dates = []
        while start_date <= end_date:
            days.append(start_date.strftime('%A'))
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
                            
        week = ["",""] + days
        header = ["Projects", "Tasks"] + dates
        
        activity_types = frappe.get_all('Activity Type', fields=['name'])
        additional_rows = []
        for activity in activity_types:
            additional_rows.append([activity['name']])
            additional_rows.append([])
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Timesheet"

        ws.append(week)
        ws.append(header)
        
        for row in projects_list:
            ws.append(row)
        
        for row in additional_rows:
            ws.append(row)

        weekend_fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")

        max_row = ws.max_row

        for col_num, day in enumerate(days, start=3):
            ws.cell(row=2, column=col_num).fill = weekend_fill
            if day in ('Saturday', 'Sunday'):
                for row_num in range(1, max_row + 1):
                    ws.cell(row=row_num, column=col_num).fill = weekend_fill

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        file_name = f"{employee_name}-{month_name}{year}-Timesheet.xlsx"

        file_url = save_file(file_name, output.read(), "Timesheet Submission", docname, is_private=0)

        return file_url

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_generation_export")
        return "error"