// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

frappe.ui.form.on("Onboarding Schedule", {
	refresh(frm) {
		frm.set_query("internship_commencement", () => ({
			filters: {
				intern: frm.doc.employee || "",
			},
		}));

		if (!frm.is_new() && frm.doc.employee) {
			frm.add_custom_button(__("View Onboarding Reports"), () => {
				frappe.route_options = {
					employee: frm.doc.employee,
				};
				frappe.set_route("onboarding-reports");
			});
		}
	},
});
