// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

frappe.query_reports["Approval Cycle Time Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -6),
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 0,
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			reqd: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		if (column.fieldname === "bottleneck") {
			if (value && value.includes("Bottleneck")) {
				value = `<span style="color:#e74c3c; font-weight:bold;">${value}</span>`;
			} else if (value && value.includes("On Track")) {
				value = `<span style="color:#27ae60;">${value}</span>`;
			} else if (value && value.includes("Pending")) {
				value = `<span style="color:#f39c12; font-weight:bold;">${value}</span>`;
			}
		}

		if (column.fieldname === "avg_days" && data.bottleneck && data.bottleneck.includes("Bottleneck")) {
			value = `<span style="color:#e74c3c; font-weight:bold;">${data.avg_days}</span>`;
		}

		if (column.fieldname === "next_step" && value && value.includes("Still in Progress")) {
			value = `<span style="color:#888; font-style:italic;">${value}</span>`;
		}

		return value;
	},

	onload: function (report) {
		// Add a helper button to explain the report
		report.page.add_inner_button(__("How to Read This Report"), function () {
			frappe.msgprint({
				title: __("Approval Cycle Time Report - Guide"),
				message: `
					<p><strong>What this report shows:</strong></p>
					<ul>
						<li>Each row = one status transition step in the approval workflow</li>
						<li><strong>Avg Days</strong> = average calendar days a requisition spent in that status before moving on</li>
						<li><strong>Bottleneck</strong> = steps taking longer than the overall average - these need attention</li>
						<li><strong>Pending</strong> = requisitions currently sitting in that status</li>
					</ul>
					<p><em>Note: Days are calendar days (including weekends).</em></p>
				`,
				indicator: "blue",
			});
		});
	},
};