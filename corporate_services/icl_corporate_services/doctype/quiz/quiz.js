// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

const QUIZ_IMPORT_TEMPLATE = `question,question_type,answer_options,correct_answer,explanation,category
What is the main purpose of the policy?,Single Select,"Promote ethics|Replace contracts|Marketing guidance",A,Pick the best answer,Policy
Which of the following apply?,Multi Select,"Option one|Option two|Option three|Option four","A|C",Select all correct choices,Policy
Describe the escalation process,Open Ended,,,Free text response,Policy
`;

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

function download_import_template() {
	const blob = new Blob([QUIZ_IMPORT_TEMPLATE], { type: "text/csv;charset=utf-8;" });
	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = "quiz_question_import_template.csv";
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
}

frappe.ui.form.on("Quiz", {
	refresh(frm) {
		render_import_help(frm);

		frm.add_custom_button("Download Import Template", () => {
			download_import_template();
		});

		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button("Import Questions", async () => {
			if (!frm.doc.question_import_file) {
				frappe.msgprint("Attach a CSV or Excel file first.");
				return;
			}

			await frappe.call({
				method: "corporate_services.icl_corporate_services.doctype.quiz.quiz.import_questions_to_quiz",
				args: {
					docname: frm.doc.name,
				},
				freeze: true,
				freeze_message: "Importing quiz questions...",
			});

			await frm.reload_doc();
			frappe.show_alert({
				message: "Questions imported into the quiz.",
				indicator: "green",
			});
		});
	},
});
