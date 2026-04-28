// Copyright (c) 2024, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timesheet Submission", {
	refresh(frm) {
		hide_finance_tab(frm);

		frappe.call({
			method: "frappe.client.get",
			args: { doctype: "Finance Settings", name: "Finance Settings" },
			callback(r) {
				const is_system_manager = frappe.user.has_role("System Manager");
				const is_finance_role = frappe.user.has_role("Finance");
				let is_finance_member = false;

				if (!r.exc && r.message) {
					const members = (r.message.table_finance_team_members || []).map(
						(m) => (m.employee_email || "").toLowerCase()
					);
					is_finance_member = members.includes(
						(frappe.session.user || "").toLowerCase()
					);
				}

				if (is_system_manager || is_finance_role || is_finance_member) {
					show_finance_tab(frm);
					compute_finance(frm);
				}
			},
		});
	},
});

function hide_finance_tab(frm) {
	frm.fields_dict["finance_tab"] &&
		$(frm.fields_dict["finance_tab"].tab_link_container).hide();
}

function show_finance_tab(frm) {
	frm.fields_dict["finance_tab"] &&
		$(frm.fields_dict["finance_tab"].tab_link_container).show();
}

function compute_finance(frm) {
	const salary = frm.doc.employee_salary || 0;
	const total_hours = frm.doc.total_working_hours || 0;

	if (salary && total_hours) {
		const per_hour = salary / (22 * 8);
		frm.doc.salary_per_hour = per_hour;
		frm.refresh_field("salary_per_hour");
	}

	const rows = frm.doc.timesheet_per_project || [];
	if (!rows.length) return;

	let html =
		'<table class="table table-bordered table-sm">' +
		"<thead><tr><th>Timesheet</th><th>Project</th><th>Month</th><th>Hours</th><th>Pay</th><th>%</th></tr></thead><tbody>";

	rows.forEach((row) => {
		html += `<tr>
			<td>${row.timesheet || ""}</td>
			<td>${row.project_name || ""}</td>
			<td>${row.month || ""}</td>
			<td>${row.total_hours || 0}</td>
			<td>${frappe.format(row.pay || 0, { fieldtype: "Currency" })}</td>
			<td>${row.percent || 0}%</td>
		</tr>`;
	});

	html += "</tbody></table>";
	frm.set_df_property("finance_breakdown_note", "options", html);
	frm.refresh_field("finance_breakdown_note");
}
