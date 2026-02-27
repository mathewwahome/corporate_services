// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

frappe.query_reports["Requisitions by Status Report"] = {
	filters: [
		{
			fieldname: "group_by",
			label: __("View By"),
			fieldtype: "Select",
			options: "Status\nDepartment\nMonth",
			default: "Status",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDRAFT\nSUBMITTED\nSUBMITTED TO HR\nSUBMITTED TO CEO\nNEEDS CLARIFICATION\nHR APPROVED\nAPPROVED FOR RECRUITMENT\nREJECTED\nCANCELLED",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		const STATUS_COLORS = {
			"APPROVED FOR RECRUITMENT": "#27ae60",
			"HR APPROVED": "#1abc9c",
			"REJECTED": "#e74c3c",
			"CANCELLED": "#95a5a6",
			"NEEDS CLARIFICATION": "#f39c12",
			"DRAFT": "#aaaaaa",
		};

		if (column.fieldname === "status" && data.status && STATUS_COLORS[data.status]) {
			const color = STATUS_COLORS[data.status];
			value = `<span style="color:${color}; font-weight:600;">${value}</span>`;
		}

		return value;
	},
};
