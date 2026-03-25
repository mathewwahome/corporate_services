// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

function render_import_help(frm) {
	const wrapper = frm.fields_dict.import_help && frm.fields_dict.import_help.$wrapper;
	if (!wrapper) {
		return;
	}

	wrapper.html(`
		<div style="padding: 12px 14px; border: 1px solid #dbe4ee; border-radius: 12px; background: #f8fafc; color: #334155;">
			<div style="font-weight: 600; margin-bottom: 6px;">Question Import Format</div>
			<div style="font-size: 12px; line-height: 1.6;">
				Use one row per question. Supported columns:
				<code>question</code>, <code>question_type</code>, <code>answer_options</code>,
				<code>correct_answer</code>, <code>explanation</code>, <code>category</code>.
				For selectable questions, separate answer options with <code>|</code> and use
				letters like <code>A</code> or <code>A|C</code> in <code>correct_answer</code>.
			</div>
		</div>
	`);
}

function build_import_summary(summary) {
	const categories = summary.categories_created || [];

	return `
		<div style="line-height: 1.7;">
			<div><strong>Quiz Import Complete</strong></div>
			<div>Created questions: ${summary.created_count || 0}</div>
			<div>Updated questions: ${summary.updated_count || 0}</div>
			<div>Skipped unchanged questions: ${summary.skipped_count || 0}</div>
			<div>Linked to this quiz: ${summary.linked_count || 0}</div>
			<div>New categories created: ${categories.length}</div>
			${categories.length ? `<div>Categories: ${frappe.utils.escape_html(categories.join(", "))}</div>` : ""}
			<div style="margin-top: 10px;">Confirm that everything looks correct on the quiz.</div>
		</div>
	`;
}

async function download_import_template(fileType) {
	const response = await frappe.call({
		method: "corporate_services.icl_corporate_services.doctype.quiz.quiz.download_quiz_import_template",
		args: {
			file_type: fileType,
		},
		freeze: true,
		freeze_message: `Preparing ${fileType.toUpperCase()} template...`,
	});

	const fileUrl = response.message && response.message.file_url;
	if (fileUrl) {
		window.open(fileUrl, "_blank");
	}
}

frappe.ui.form.on("Quiz", {
	refresh(frm) {
		render_import_help(frm);

		frm.add_custom_button("Download CSV Template", async () => {
			await download_import_template("csv");
		});

		frm.add_custom_button("Download Excel Template", async () => {
			await download_import_template("xlsx");
		});

		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button("Import Questions", async () => {
			if (!frm.doc.question_import_file) {
				frappe.msgprint("Attach a CSV or Excel file first.");
				return;
			}

			const response = await frappe.call({
				method: "corporate_services.icl_corporate_services.doctype.quiz.quiz.import_questions_to_quiz",
				args: {
					docname: frm.doc.name,
				},
				freeze: true,
				freeze_message: "Importing quiz questions...",
			});

			await frm.reload_doc();
			frappe.msgprint({
				title: "Import Summary",
				indicator: "green",
				message: build_import_summary(response.message || {}),
			});
		});
	},
});
