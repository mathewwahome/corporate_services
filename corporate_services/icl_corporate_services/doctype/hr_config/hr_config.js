// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reminder Rule", {
	reference_doctype: function (frm, cdt, cdn) {
		corporate_services.reminder_rule.set_field_options(frm, cdt, cdn);
	},

	form_render: function (frm, cdt, cdn) {
		corporate_services.reminder_rule.set_field_options(frm, cdt, cdn);
	},
});

frappe.provide("corporate_services.reminder_rule");

corporate_services.reminder_rule = {
	// The grid field that embeds this child doctype, e.g. HR Config's "reminder_rules".
	get_grid_field: function (frm, cdt) {
		return Object.values(frm.fields_dict).find(
			(f) => f.df.fieldtype === "Table" && f.df.options === cdt
		);
	},

	set_field_options: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const grid_field = corporate_services.reminder_rule.get_grid_field(frm, cdt);
		if (!row.reference_doctype || !grid_field) {
			return;
		}

		frappe.model.with_doctype(row.reference_doctype, function () {
			const doctype_fields = frappe.get_doc("DocType", row.reference_doctype).fields;
			const link_fields_to = (targets) =>
				[""].concat(
					doctype_fields
						.filter((df) => df.fieldtype === "Link" && targets.includes(df.options))
						.map((df) => df.fieldname)
				);

			// Update only this row's own docfield copies, not the whole grid column,
			// so each row can show options for its own Reference Doctype.
			const grid_row = grid_field.grid.grid_rows_by_docname[cdn];
			if (!grid_row) {
				return;
			}

			const employee_field_options = link_fields_to(["Employee"]);
			const approver_field_options = link_fields_to(["Employee", "User"]);

			grid_row.docfields.forEach((df) => {
				if (df.fieldname === "employee_field") {
					df.options = employee_field_options;
				} else if (df.fieldname === "approver_field") {
					df.options = approver_field_options;
				}
			});

			grid_row.refresh_field("employee_field");
			grid_row.refresh_field("approver_field");
		});
	},
};
