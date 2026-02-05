# Copyright (c) 2026, ICL Corporate Services and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, cstr

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data)
    
    return columns, data, None, chart

def get_columns(filters):
    """Define the columns for the report"""
    columns = [
        {
            "fieldname": "name",
            "label": _("Timesheet ID"),
            "fieldtype": "Link",
            "options": "Timesheet Submission",
            "width": 150
        },
        {
            "fieldname": "employee",
            "label": _("Employee ID"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "width": 150
        },
        {
            "fieldname": "designation",
            "label": _("Designation"),
            "fieldtype": "Link",
            "options": "Designation",
            "width": 150
        },
        {
            "fieldname": "month_year",
            "label": _("Month-Year"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_working_hours",
            "label": _("Total Hours"),
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "project_count",
            "label": _("No. of Projects"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "submission_date",
            "label": _("Submitted On"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "timesheet_imported",
            "label": _("Imported"),
            "fieldtype": "Check",
            "width": 80
        },
        {
            "fieldname": "owner",
            "label": _("Submitted By"),
            "fieldtype": "Data",
            "width": 150
        }
    ]
    
    return columns

def get_data(filters):
    """Fetch and process the timesheet submission data"""
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            ts.name,
            ts.employee,
            ts.employee_name,
            emp.department,
            emp.designation,
            ts.month_year,
            ts.total_working_hours,
            ts.status,
            ts.timesheet_imported,
            ts.creation as submission_date,
            ts.owner,
            (SELECT COUNT(*) 
             FROM `tabTimesheet Submission List` 
             WHERE parent = ts.name) as project_count
        FROM 
            `tabTimesheet Submission` ts
        LEFT JOIN
            `tabEmployee` emp ON ts.employee = emp.name
        WHERE
            ts.docstatus != 2
            {conditions}
        ORDER BY 
            ts.creation DESC
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    """Build SQL conditions based on filters"""
    conditions = []
    
    if filters.get("employee"):
        conditions.append("ts.employee = %(employee)s")
    
    if filters.get("month_year"):
        conditions.append("ts.month_year = %(month_year)s")
    
    if filters.get("status"):
        conditions.append("ts.status = %(status)s")
    
    if filters.get("department"):
        conditions.append("emp.department = %(department)s")
    
    if filters.get("designation"):
        conditions.append("emp.designation = %(designation)s")
    
    if filters.get("from_date"):
        conditions.append("ts.creation >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("ts.creation <= %(to_date)s")
    
    if filters.get("timesheet_imported"):
        conditions.append("ts.timesheet_imported = %(timesheet_imported)s")
    
    return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
    """Generate chart data for visualization"""
    if not data:
        return None
    
    # Employee total hours per month-year
    employee_month_hours = {}
    
    for row in data:
        employee_name = row.get('employee_name') or 'Unknown'
        month_year = row.get('month_year') or 'Unknown'
        key = f"{employee_name}"
        
        if key not in employee_month_hours:
            employee_month_hours[key] = {}
        
        if month_year not in employee_month_hours[key]:
            employee_month_hours[key][month_year] = 0
        
        # Use total_working_hours directly (each row is unique timesheet)
        employee_month_hours[key][month_year] = row.get('total_working_hours', 0)
    
    # Get all unique month-years sorted
    all_months = sorted(set(
        month for employee_data in employee_month_hours.values() 
        for month in employee_data.keys()
    ))
    
    # Prepare datasets for each employee
    datasets = []
    colors = ["#7cd6fd", "#5e64ff", "#743ee2", "#ff5858", "#ffa00a", 
              "#28a745", "#17a2b8", "#ffc107", "#dc3545", "#6c757d",
              "#20c997", "#e83e8c", "#fd7e14", "#6610f2", "#007bff"]
    
    for idx, (employee, month_data) in enumerate(employee_month_hours.items()):
        values = [month_data.get(month, 0) for month in all_months]
        datasets.append({
            "name": employee,
            "values": values
        })
    
    chart = {
        "data": {
            "labels": all_months,
            "datasets": datasets
        },
        "type": "bar",
        "height": 350,
        "colors": colors,
        "barOptions": {
            "stacked": 0
        },
        "axisOptions": {
            "xAxisMode": "tick",
            "xIsSeries": 1
        }
    }
    
    return chart