// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee KPI", {
	refresh(frm) {
		frm.add_custom_button(__("KPI Template Instructions"), () => {
			frappe.set_route("Form", "KPI Template Instructions");
		});
	},
});
