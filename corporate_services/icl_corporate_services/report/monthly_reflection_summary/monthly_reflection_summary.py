import frappe
from datetime import datetime


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Month",       "fieldname": "month",     "fieldtype": "Data",    "width": 130},
        {"label": "Submitted",   "fieldname": "submitted", "fieldtype": "Int",     "width": 100},
        {"label": "Total Staff", "fieldname": "total",     "fieldtype": "Int",     "width": 100},
        {"label": "Missing",     "fieldname": "missing",   "fieldtype": "Int",     "width": 100},
        {"label": "% Complete",  "fieldname": "pct",       "fieldtype": "Percent", "width": 110},
    ]

    all_employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "designation", "department", "custom_reports_to_name"]
    )
    total_staff = len(all_employees)
    employee_ids = {e.name for e in all_employees}

    year = filters.get("year") or str(datetime.now().year)

    reflections = frappe.get_all(
        "Monthly Reflection",
        filters=[["review_period", "like", f"%{year}%"]],
        fields=["employee", "review_period"]
    )

    period_map = {}
    for r in reflections:
        period_map.setdefault(r.review_period, set()).add(r.employee)

    data = []
    for period in sorted(period_map.keys()):
        active_submitters = period_map[period] & employee_ids
        submitted = len(active_submitters)
        missing = total_staff - submitted
        pct = round((submitted / total_staff) * 100, 1) if total_staff else 0
        data.append({
            "month":     period,
            "submitted": submitted,
            "total":     total_staff,
            "missing":   missing,
            "pct":       pct
        })

    return columns, data


def get_filters():
    years_raw = frappe.db.sql("""
        SELECT DISTINCT SUBSTRING(review_period, -4) AS yr
        FROM `tabMonthly Reflection`
        WHERE review_period IS NOT NULL
          AND review_period != ''
        ORDER BY yr DESC
    """, as_dict=True)

    current_year = str(datetime.now().year)
    year_list = [row.yr for row in years_raw if row.yr and row.yr.isdigit()]

    if current_year not in year_list:
        year_list.insert(0, current_year)

    options = "\n".join(year_list)

    return [
        {
            "fieldname": "year",
            "label": "Year",
            "fieldtype": "Select",
            "options": "\n" + options,
            "default": current_year
        }
    ]