// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

const MONTH_NAMES = [
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December",
];

frappe.ui.form.on("Monthly Reflection", {
	setup(frm) {
		set_review_period_options(frm);
	},

	refresh(frm) {
		set_review_period_options(frm);
	},
});

function set_review_period_options(frm) {
	const current_date = frappe.datetime.str_to_obj(frappe.datetime.nowdate());
	const current_year = current_date.getFullYear();
	const options = [""];

	for (let year = current_year + 2; year >= current_year - 2; year--) {
		for (let month_index = MONTH_NAMES.length - 1; month_index >= 0; month_index--) {
			options.push(`${MONTH_NAMES[month_index]} ${year}`);
		}
	}

	if (frm.doc.review_period && !options.includes(frm.doc.review_period)) {
		options.unshift(frm.doc.review_period);
	}

	frm.set_df_property("review_period", "options", options.join("\n"));
}
