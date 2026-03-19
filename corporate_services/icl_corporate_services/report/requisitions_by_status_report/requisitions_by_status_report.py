# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


STATUS_ORDER = [
    "DRAFT",
    "SUBMITTED",
    "SUBMITTED TO HR",
    "SUBMITTED TO CEO",
    "NEEDS CLARIFICATION",
    "HR APPROVED",
    "APPROVED FOR RECRUITMENT",
    "REJECTED",
    "CANCELLED",
]

STATUS_COLORS = {
    "DRAFT": "#d3d3d3",
    "SUBMITTED": "#5e64ff",
    "SUBMITTED TO HR": "#7575ff",
    "SUBMITTED TO CEO": "#9b59b6",
    "NEEDS CLARIFICATION": "#f39c12",
    "HR APPROVED": "#1abc9c",
    "APPROVED FOR RECRUITMENT": "#27ae60",
    "REJECTED": "#e74c3c",
    "CANCELLED": "#95a5a6",
}


def execute(filters=None):
    filters = filters or {}
    mode = filters.get("group_by", "Status")

    if mode == "Department":
        columns, data = get_by_department(filters)
        chart = get_dept_chart(data)
    elif mode == "Month":
        columns, data = get_by_month(filters)
        chart = get_month_chart(data, filters)
    else:
        columns, data = get_by_status(filters)
        chart = get_status_chart(data)

    summary = get_summary(filters)
    return columns, data, None, chart, summary


# BY STATUS 

def get_by_status(filters):
    columns = [
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 230},
        {"label": _("Count"), "fieldname": "count", "fieldtype": "Int", "width": 100},
        {"label": _("% of Total"), "fieldname": "pct", "fieldtype": "Percent", "width": 120},
    ]

    conditions, values = build_conditions(filters)
    rows = frappe.db.sql(
        """
        SELECT status, COUNT(*) AS count
        FROM `tabStaff Requisition`
        {where}
        GROUP BY status
        """.format(where=conditions),
        values,
        as_dict=True,
    )

    total = sum(r.count for r in rows)
    status_map = {r.status: r.count for r in rows}

    data = []
    for s in STATUS_ORDER:
        if s in status_map:
            data.append({
                "status": s,
                "count": status_map[s],
                "pct": round(status_map[s] / total * 100, 1) if total else 0,
            })
    for r in rows:
        if r.status not in STATUS_ORDER:
            data.append({
                "status": r.status or "(None)",
                "count": r.count,
                "pct": round(r.count / total * 100, 1) if total else 0,
            })

    return columns, data


def get_status_chart(data):
    if not data:
        return None
    return {
        "data": {
            "labels": [r["status"] for r in data],
            "datasets": [{"values": [r["count"] for r in data]}],
        },
        "type": "donut",
        "colors": [STATUS_COLORS.get(r["status"], "#aaaaaa") for r in data],
        "title": "Requisitions by Status",
    }


# BY DEPARTMENT 

def get_by_department(filters):
    active_statuses = frappe.db.sql(
        "SELECT DISTINCT status FROM `tabStaff Requisition` WHERE status IS NOT NULL ORDER BY status",
        as_dict=True,
    )
    present_statuses = [r.status for r in active_statuses if r.status]

    columns = [
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 200},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 80},
    ]
    for s in STATUS_ORDER:
        if s in present_statuses:
            columns.append({
                "label": _(s.title()),
                "fieldname": "status_" + s.lower().replace(" ", "_"),
                "fieldtype": "Int",
                "width": 140,
            })

    conditions, values = build_conditions(filters)
    rows = frappe.db.sql(
        """
        SELECT department, status, COUNT(*) AS count
        FROM `tabStaff Requisition`
        {where}
        GROUP BY department, status
        ORDER BY department
        """.format(where=conditions),
        values,
        as_dict=True,
    )

    dept_map = {}
    for r in rows:
        dept = r.department or "(No Department)"
        if dept not in dept_map:
            dept_map[dept] = {"department": dept, "total": 0}
        dept_map[dept]["total"] += r.count
        key = "status_" + (r.status or "").lower().replace(" ", "_")
        dept_map[dept][key] = dept_map[dept].get(key, 0) + r.count

    data = sorted(dept_map.values(), key=lambda x: x["department"])
    return columns, data


def get_dept_chart(data):
    if not data:
        return None
    labels = [r["department"] for r in data]
    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Total", "values": [r["total"] for r in data]}],
        },
        "type": "bar",
        "colors": ["#5e64ff"],
        "title": "Requisitions by Department",
    }


# BY MONTH 

def get_by_month(filters):
    columns = [
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 120},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 180},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 200},
        {"label": _("Count"), "fieldname": "count", "fieldtype": "Int", "width": 90},
    ]

    conditions, values = build_conditions(filters)
    rows = frappe.db.sql(
        """
        SELECT
            DATE_FORMAT(date_of_request, '%%Y-%%m') AS month,
            department,
            status,
            COUNT(*) AS count
        FROM `tabStaff Requisition`
        {where}
        GROUP BY month, department, status
        ORDER BY month, department, status
        """.format(where=conditions),
        values,
        as_dict=True,
    )

    data = []
    for r in rows:
        data.append({
            "month": r.month,
            "department": r.department or "(No Department)",
            "status": r.status or "(None)",
            "count": r.count,
        })

    return columns, data


def get_month_chart(data, filters):
    if not data:
        return None

    # Aggregate total per month for the chart
    month_totals = {}
    for r in data:
        month_totals[r["month"]] = month_totals.get(r["month"], 0) + r["count"]

    months = sorted(month_totals.keys())

    # Build per-status datasets
    status_data = {}
    for r in data:
        s = r["status"]
        if s not in status_data:
            status_data[s] = {m: 0 for m in months}
        status_data[s][r["month"]] = status_data[s].get(r["month"], 0) + r["count"]

    datasets = []
    for s in STATUS_ORDER:
        if s in status_data:
            datasets.append({
                "name": s,
                "values": [status_data[s].get(m, 0) for m in months],
            })

    return {
        "data": {
            "labels": months,
            "datasets": datasets,
        },
        "type": "bar",
        "colors": [STATUS_COLORS.get(s, "#aaa") for s in STATUS_ORDER if s in status_data],
        "title": "Requisitions by Month & Status",
        "barOptions": {"stacked": True},
    }


# HELPERS

def build_conditions(filters):
    conditions = []
    values = {}
    if filters.get("from_date"):
        conditions.append("date_of_request >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("date_of_request <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("department"):
        conditions.append("department = %(department)s")
        values["department"] = filters["department"]
    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters["status"]
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, values


def get_summary(filters):
    conditions, values = build_conditions(filters)
    totals = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'APPROVED FOR RECRUITMENT' THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected,
            SUM(CASE WHEN status NOT IN ('APPROVED FOR RECRUITMENT','REJECTED','CANCELLED') THEN 1 ELSE 0 END) AS in_progress
        FROM `tabStaff Requisition`
        {where}
        """.format(where=conditions),
        values,
        as_dict=True,
    )
    t = totals[0] if totals else {}
    return [
        {"label": "Total Requisitions", "value": t.get("total", 0), "indicator": "Blue"},
        {"label": "Approved", "value": t.get("approved", 0), "indicator": "Green"},
        {"label": "Rejected", "value": t.get("rejected", 0), "indicator": "Red"},
        {"label": "In Progress", "value": t.get("in_progress", 0), "indicator": "Orange"},
    ]