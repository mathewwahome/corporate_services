import frappe
from frappe.utils.file_manager import save_file
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side
from io import BytesIO
import calendar

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
            
        last_day = calendar.monthrange(previous_year, previous_month)[1]


        # start_date = datetime(previous_year, previous_month, 29).date()
        start_date = datetime(previous_year, previous_month, min(29, last_day)).date()
        
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

        wb = Workbook()
        ws = wb.active
        ws.title = "Timesheet"

        week = ["", ""] + days
        header = ["Projects", "Tasks"] + dates
        ws.append(week)
        ws.append(header)
        
        # Track project name row numbers
        project_rows = []
        current_row = 3
        
        for row in projects_list:
            ws.append(row)
            if row and row[0]:
                project_rows.append(current_row)
            current_row += 1

        blue_fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")
        yellow_fill = PatternFill(start_color="FFEB3B", end_color="FFEB3B", fill_type="solid")

        thin_border = Border(
            left=Side(style='thin', color="000000"),
            right=Side(style='thin', color="000000"),
            top=Side(style='thin', color="000000"),
            bottom=Side(style='thin', color="000000")
        )

        # Apply blue fill to header row
        for col_num in range(1, len(header) + 1):
            cell = ws.cell(row=2, column=col_num)
            cell.fill = blue_fill
            cell.border = thin_border

        # Apply blue fill to project name rows
        for row_num in project_rows:
            for col_num in range(1, len(header) + 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.fill = blue_fill
                cell.border = thin_border

        # Get only enabled activity types
        activity_types = frappe.get_all('Activity Type', filters={'disabled': 0}, fields=['name'])
        activity_types = [activity for activity in activity_types if activity['name'].lower() != "projects"]

        activity_rows_start = len(projects_list) + 3
        activity_rows = []
        
        for i, activity in enumerate(activity_types):
            row_num = activity_rows_start + i * 2
            ws.cell(row=row_num, column=1, value=activity['name'])
            activity_rows.append(row_num)
        
        # Get current max row and add 3 empty rows
        current_max_row = ws.max_row
        for i in range(3):
            empty_row_num = current_max_row + 1 + i
            # Add empty cells to ensure the row exists
            for col_num in range(1, len(header) + 1):
                ws.cell(row=empty_row_num, column=col_num, value="")
        
        max_row = ws.max_row
        
        # Apply blue fill to weekend columns
        for col_num, day in enumerate(days, start=3):
            if day in ('Saturday', 'Sunday'):
                for row_num in range(1, max_row + 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.fill = blue_fill
                    cell.border = thin_border

        # Apply blue fill to activity type rows
        for row_num in activity_rows:
            for col_num in range(1, len(header) + 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.fill = blue_fill
                cell.border = thin_border

        # Apply borders to all cells
        for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=len(header)):
            for cell in row:
                cell.border = thin_border
                
        # Add total row at the bottom
        total_row = max_row + 1
        ws.cell(row=total_row, column=1, value="TOTAL")
        ws.cell(row=total_row, column=1).fill = blue_fill
        ws.cell(row=total_row, column=2).fill = blue_fill
        
        # Add SUM formulas for each day column
        for col_num in range(3, len(header) + 1):
            col_letter = ws.cell(row=1, column=col_num).column_letter
            # Formula to sum all numeric values in the column excluding headers and the total row itself
            formula = f"=SUM({col_letter}3:{col_letter}{max_row})"
            ws.cell(row=total_row, column=col_num, value=formula)
            ws.cell(row=total_row, column=col_num).fill = blue_fill
            ws.cell(row=total_row, column=col_num).border = thin_border
        
        # Add total hours row at the bottom
        total_hours_row = total_row + 1
        ws.cell(row=total_hours_row, column=1, value="TOTAL HRS")
        ws.cell(row=total_hours_row, column=1).fill = blue_fill
        ws.cell(row=total_hours_row, column=2).fill = blue_fill
        ws.cell(row=total_hours_row, column=2).border = thin_border
        
        # Calculate sum of all daily totals
        start_col_letter = ws.cell(row=1, column=3).column_letter
        end_col_letter = ws.cell(row=1, column=len(header)).column_letter
        total_hours_formula = f"=SUM({start_col_letter}{total_row}:{end_col_letter}{total_row})"
        ws.cell(row=total_hours_row, column=3, value=total_hours_formula)
        ws.cell(row=total_hours_row, column=3).fill = blue_fill
        ws.cell(row=total_hours_row, column=3).border = thin_border
        
        # Apply borders to total hours row
        for col_num in range(1, len(header) + 1):
            ws.cell(row=total_hours_row, column=col_num).border = thin_border

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        file_name = f"{employee_name}-{month_name}{year}-Timesheet.xlsx"
        file_url = save_file(file_name, output.read(), "Timesheet Submission", docname, is_private=0)

        return file_url

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "timesheet_generation_export")
        return "error"