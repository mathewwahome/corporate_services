import frappe
from datetime import datetime


MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
STATUSES = ["Open", "Approved", "Rejected", "Cancelled"]
COLORS = {
    "Open": "#f59e0b",
    "Approved": "#16a34a",
    "Rejected": "#dc2626",
    "Cancelled": "#64748b",
}


def execute(filters=None):
    filters = filters or {}
    year = cint(filters.get("year")) or datetime.now().year

    columns = get_columns()
    data = get_data(year)
    chart = get_chart_data(data)

    return columns, data, None, chart


def get_columns():
    return [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 90},
        {"label": "Open", "fieldname": "open_count", "fieldtype": "Int", "width": 90},
        {"label": "Approved", "fieldname": "approved_count", "fieldtype": "Int", "width": 100},
        {"label": "Rejected", "fieldname": "rejected_count", "fieldtype": "Int", "width": 100},
        {"label": "Cancelled", "fieldname": "cancelled_count", "fieldtype": "Int", "width": 100},
        {"label": "Total", "fieldname": "total_count", "fieldtype": "Int", "width": 90},
    ]


def get_data(year):
    rows = frappe.db.sql(
        """
        SELECT month_year, status
        FROM `tabTimesheet Submission`
        WHERE docstatus != 2
          AND month_year IS NOT NULL
          AND month_year != ''
        """,
        as_dict=True,
    )

    month_totals = {
        month_index: {status: 0 for status in STATUSES}
        for month_index in range(1, 13)
    }

    for row in rows:
        parsed = parse_month_year(row.get("month_year"))
        if not parsed or parsed["year"] != year:
            continue

        status = row.get("status") if row.get("status") in STATUSES else "Open"
        month_totals[parsed["month"]][status] += 1

    data = []
    for month_index in range(1, 13):
        counts = month_totals[month_index]
        total = sum(counts.values())
        data.append(
            {
                "month": MONTH_LABELS[month_index - 1],
                "open_count": counts["Open"],
                "approved_count": counts["Approved"],
                "rejected_count": counts["Rejected"],
                "cancelled_count": counts["Cancelled"],
                "total_count": total,
            }
        )

    return data


def get_chart_data(data):
    return {
        "data": {
            "labels": [row["month"] for row in data],
            "datasets": [
                {"name": "Open", "values": [row["open_count"] for row in data]},
                {"name": "Approved", "values": [row["approved_count"] for row in data]},
                {"name": "Rejected", "values": [row["rejected_count"] for row in data]},
                {"name": "Cancelled", "values": [row["cancelled_count"] for row in data]},
            ],
        },
        "type": "bar",
        "height": 320,
        "colors": [COLORS[status] for status in STATUSES],
        "barOptions": {"stacked": 1},
        "axisOptions": {"xAxisMode": "tick", "xIsSeries": 1},
    }


def parse_month_year(value):
    if not value or "-" not in value:
        return None

    try:
        month_str, year_str = value.split("-", 1)
        month = int(month_str)
        year = int(year_str)
    except (TypeError, ValueError):
        return None

    if month < 1 or month > 12:
        return None

    return {"month": month, "year": year}


def cint(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
