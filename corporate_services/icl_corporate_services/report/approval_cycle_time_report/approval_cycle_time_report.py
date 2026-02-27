# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, now_datetime, getdate


TERMINAL_STATUSES = {"APPROVED FOR RECRUITMENT", "REJECTED", "CANCELLED"}

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


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data, meta = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data, meta)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Approval Step"),
            "fieldname": "step",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Requisitions"),
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Avg Days"),
            "fieldname": "avg_days",
            "fieldtype": "Float",
            "precision": 1,
            "width": 110,
        },
        {
            "label": _("Min Days"),
            "fieldname": "min_days",
            "fieldtype": "Float",
            "precision": 1,
            "width": 100,
        },
        {
            "label": _("Max Days"),
            "fieldname": "max_days",
            "fieldtype": "Float",
            "precision": 1,
            "width": 100,
        },
        {
            "label": _("Still Waiting"),
            "fieldname": "still_waiting",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Bottleneck"),
            "fieldname": "bottleneck",
            "fieldtype": "Data",
            "width": 130,
        },
    ]


def get_data(filters):
    # 1. Fetch all Staff Requisitions matching filters
    sr_conditions = []
    sr_values = {}

    if filters.get("from_date"):
        sr_conditions.append("sr.date_of_request >= %(from_date)s")
        sr_values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        sr_conditions.append("sr.date_of_request <= %(to_date)s")
        sr_values["to_date"] = filters["to_date"]
    if filters.get("department"):
        sr_conditions.append("sr.department = %(department)s")
        sr_values["department"] = filters["department"]

    where = ("WHERE " + " AND ".join(sr_conditions)) if sr_conditions else ""

    requisitions = frappe.db.sql(
        """
        SELECT sr.name, sr.creation, sr.status, sr.department, sr.date_of_request
        FROM `tabStaff Requisition` sr
        {where}
        ORDER BY sr.creation
        """.format(where=where),
        sr_values,
        as_dict=True,
    )

    if not requisitions:
        return [], {}

    req_map = {r.name: r for r in requisitions}
    req_names = list(req_map.keys())

    # 2. Fetch all approval log rows for these requisitions
    approval_rows = frappe.db.sql(
        """
        SELECT
            a.parent,
            a.title      AS step,
            a.datetime   AS actioned_at,
            a.idx
        FROM `tabStaff Requisition Approval` a
        WHERE a.parent IN %(names)s
        ORDER BY a.parent, a.idx ASC, a.datetime ASC
        """,
        {"names": req_names},
        as_dict=True,
    )

    # Group approval rows by requisition
    logs_by_req = {}
    for row in approval_rows:
        logs_by_req.setdefault(row.parent, []).append(row)

    # 3. Build per-step duration records
    step_records = []

    for req in requisitions:
        logs = logs_by_req.get(req.name, [])
        is_terminal = (req.status or "").upper() in TERMINAL_STATUSES

        if not logs:
            # No approvals yet - count days since creation in current status
            days = _diff_days(req.creation, now_datetime())
            step_records.append({
                "step": req.status or "DRAFT",
                "days": days,
                "docname": req.name,
                "is_open": not is_terminal,
            })
            continue

        # Duration from requisition creation to first approval action
        first_dt = logs[0].actioned_at
        days = _diff_days(req.creation, first_dt)
        step_records.append({
            "step": "Initial Review",
            "days": days,
            "docname": req.name,
            "is_open": False,
        })

        # Duration between consecutive approval steps
        for i in range(len(logs)):
            current_log = logs[i]
            step_name = current_log.step or "Step {}".format(i + 1)
            from_dt = current_log.actioned_at

            if i + 1 < len(logs):
                to_dt = logs[i + 1].actioned_at
                is_open = False
            else:
                to_dt = now_datetime() if not is_terminal else req.creation
                is_open = not is_terminal

            days = _diff_days(from_dt, to_dt)
            step_records.append({
                "step": step_name,
                "days": days,
                "docname": req.name,
                "is_open": is_open,
            })

    if not step_records:
        return [], {}

    agg = {}
    for rec in step_records:
        s = rec["step"]
        if s not in agg:
            agg[s] = {"durations": [], "waiting": 0}
        if rec["days"] >= 0:
            agg[s]["durations"].append(rec["days"])
        if rec["is_open"]:
            agg[s]["waiting"] += 1

    rows = []
    for step, vals in agg.items():
        d = vals["durations"]
        if not d:
            continue
        avg = sum(d) / len(d)
        rows.append({
            "step": step,
            "total": len(d),
            "avg_days": round(avg, 1),
            "min_days": round(min(d), 1),
            "max_days": round(max(d), 1),
            "still_waiting": vals["waiting"],
            "bottleneck": "",
        })

    def sort_key(r):
        for i, s in enumerate(STATUS_ORDER):
            if s in r["step"].upper():
                return (i, r["step"])
        return (999, r["step"])

    rows.sort(key=sort_key)

    # Mark bottlenecks (steps above overall average)
    if rows:
        overall_avg = sum(r["avg_days"] for r in rows) / len(rows)
        for r in rows:
            if r["still_waiting"] > 0 and r["avg_days"] > overall_avg:
                r["bottleneck"] = "Bottleneck"
            elif r["still_waiting"] > 0:
                r["bottleneck"] = "Awaiting"
            elif r["avg_days"] > overall_avg:
                r["bottleneck"] = "Slow"
            else:
                r["bottleneck"] = "On Track"

    meta = {
        "total_reqs": len(requisitions),
        "overall_avg": round(sum(r["avg_days"] for r in rows) / max(len(rows), 1), 1),
        "bottlenecks": len([r for r in rows if "Bottleneck" in r["bottleneck"]]),
        "waiting": sum(r["still_waiting"] for r in rows),
    }

    return rows, meta


def _diff_days(from_dt, to_dt):
    try:
        if not from_dt or not to_dt:
            return 0
        from_date = getdate(str(from_dt)[:10])
        to_date = getdate(str(to_dt)[:10])
        return max(date_diff(to_date, from_date), 0)
    except Exception:
        return 0


def get_chart(data):
    if not data:
        return None
    labels = [r["step"] for r in data]
    avg_vals = [r["avg_days"] for r in data]
    max_vals = [r["max_days"] for r in data]
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Avg Days", "values": avg_vals},
                {"name": "Max Days", "values": max_vals},
            ],
        },
        "type": "bar",
        "colors": ["#5e64ff", "#ff6b6b"],
        "title": "Avg Days per Approval Step",
        "axisOptions": {"xIsSeries": True},
    }


def get_summary(data, meta):
    if not meta:
        return []
    return [
        {"label": "Requisitions", "value": meta.get("total_reqs", 0), "indicator": "Blue"},
        {"label": "Avg Days / Step", "value": meta.get("overall_avg", 0), "indicator": "Orange"},
        {"label": "Bottleneck Steps", "value": meta.get("bottlenecks", 0), "indicator": "Red" if meta.get("bottlenecks") else "Green"},
        {"label": "Currently Waiting", "value": meta.get("waiting", 0), "indicator": "Orange" if meta.get("waiting") else "Green"},
    ]