// Copyright (c) 2026, ICL Corporate Services and contributors
// For license information, please see license.txt

frappe.query_reports["Timesheet Submission Report"] = {
    "filters": [
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 100,
            "get_query": function() {
                return {
                    "filters": {
                        "status": "Active"
                    }
                }
            }
        },
        {
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "width": 100
        },
        {
            "fieldname": "designation",
            "label": __("Designation"),
            "fieldtype": "Link",
            "options": "Designation",
            "width": 100
        },
        {
            "fieldname": "month_year",
            "label": __("Month-Year"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": ["", "Open", "Approved", "Rejected", "Cancelled"],
            "default": "",
            "width": 100
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "width": 100,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "width": 100,
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "timesheet_imported",
            "label": __("Imported Only"),
            "fieldtype": "Check",
            "width": 100
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Color code status
        if (column.fieldname == "status") {
            if (value == "Approved") {
                value = "<span style='color:green; font-weight:bold'>" + value + "</span>";
            } else if (value == "Rejected" || value == "Cancelled") {
                value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
            } else if (value == "Open") {
                value = "<span style='color:orange; font-weight:bold'>" + value + "</span>";
            }
        }
        
        // Highlight high working hours
        if (column.fieldname == "total_working_hours" && data && data.total_working_hours > 200) {
            value = "<span style='color:blue; font-weight:bold'>" + value + "</span>";
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons
        report.page.add_inner_button(__("Export Approved Timesheets"), function() {
            let filters = report.get_values();
            filters.status = "Approved";
            frappe.query_report.refresh();
        });
        
        report.page.add_inner_button(__("Send Reminder"), function() {
            frappe.call({
                method: "your_app.api.send_timesheet_reminder",
                args: {
                    filters: report.get_values()
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__("Reminders sent successfully"));
                    }
                }
            });
        });
    }
};