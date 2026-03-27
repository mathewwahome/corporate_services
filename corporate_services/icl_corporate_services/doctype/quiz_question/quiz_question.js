// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

let quiz_question_styles_added = false;

function ensure_quiz_question_styles() {
	if (quiz_question_styles_added) {
		return;
	}

	const style = document.createElement("style");
	style.textContent = `
		.quiz-answer-selector-empty {
			padding: 16px;
			border: 1px dashed #cbd5e1;
			border-radius: 12px;
			background: #f8fafc;
			color: #64748b;
		}

		.quiz-answer-selector-list {
			display: grid;
			gap: 10px;
		}

		.quiz-answer-selector-option {
			display: flex;
			align-items: flex-start;
			gap: 12px;
			padding: 12px 14px;
			border: 1px solid #dbe4ee;
			border-radius: 12px;
			background: #ffffff;
		}

		.quiz-answer-selector-option input {
			margin-top: 3px;
		}

		.quiz-answer-selector-code {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			width: 24px;
			height: 24px;
			border-radius: 999px;
			background: #eff6ff;
			color: #1d4ed8;
			font-size: 12px;
			font-weight: 700;
			flex-shrink: 0;
		}

		.quiz-answer-selector-text {
			line-height: 1.5;
			color: #0f172a;
		}

		.quiz-answer-selector-help {
			margin-top: 10px;
			font-size: 12px;
			color: #64748b;
		}
	`;

	document.head.appendChild(style);
	quiz_question_styles_added = true;
}

function escape_html(value) {
	return String(value || "")
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

function get_answer_options(frm) {
	return (frm.doc.answer_options || "")
		.split(/\r?\n/)
		.map((value) => value.trim())
		.filter(Boolean);
}

function split_correct_answers(value) {
	return (value || "")
		.replace(/\|\|\|/g, "\n")
		.replace(/,/g, "\n")
		.split(/\r?\n/)
		.map((item) => item.trim().toUpperCase())
		.filter(Boolean);
}

function get_option_code(index) {
	return String.fromCharCode(65 + index);
}

function set_correct_answer_from_selector(frm, selected_codes) {
	const normalized_codes = selected_codes
		.map((code) => code.trim().toUpperCase())
		.filter(Boolean);

	frm.set_value("correct_answer", normalized_codes.join("\n"));
}

function render_correct_answer_selector(frm) {
	ensure_quiz_question_styles();

	const wrapper = frm.fields_dict.correct_answer_selector && frm.fields_dict.correct_answer_selector.$wrapper;
	if (!wrapper) {
		return;
	}

	const question_type = frm.doc.question_type || "Single Select";
	if (!["Single Select", "Multi Select"].includes(question_type)) {
		wrapper.html(`
			<div class="quiz-answer-selector-empty">
				Open ended questions do not need a predefined correct answer.
			</div>
		`);
		return;
	}

	const options = get_answer_options(frm);
	if (!options.length) {
		wrapper.html(`
			<div class="quiz-answer-selector-empty">
				Add answer options first. Each line in <strong>Answer Options</strong> becomes option A, B, C and so on.
			</div>
		`);
		return;
	}

	const selected_codes = split_correct_answers(frm.doc.correct_answer);
	const input_type = question_type === "Multi Select" ? "checkbox" : "radio";
	const help_text =
		question_type === "Multi Select"
			? "Select every correct option. The stored value will be A, B, C and so on."
			: "Select the one correct option. The stored value will be A, B, C and so on.";

	wrapper.html(`
		<div class="quiz-answer-selector-list">
			${options
				.map((option, index) => {
					const code = get_option_code(index);
					const checked = selected_codes.includes(code) ? "checked" : "";

					return `
						<label class="quiz-answer-selector-option">
							<input
								type="${input_type}"
								name="correct-answer-selector"
								data-code="${code}"
								${checked}
							/>
							<span class="quiz-answer-selector-code">${code}</span>
							<span class="quiz-answer-selector-text">${escape_html(option)}</span>
						</label>
					`;
				})
				.join("")}
		</div>
		<div class="quiz-answer-selector-help">${help_text}</div>
	`);

	wrapper.off(".quiz_question_selector");
	wrapper.on("change.quiz_question_selector", "input[data-code]", function () {
		if (input_type === "radio") {
			set_correct_answer_from_selector(frm, [this.dataset.code || ""]);
			return;
		}

		const selected = [];
		wrapper.find("input[data-code]:checked").each(function () {
			selected.push(this.dataset.code || "");
		});
		set_correct_answer_from_selector(frm, selected);
	});
}

frappe.ui.form.on("Quiz Question", {
	refresh(frm) {
		render_correct_answer_selector(frm);
	},

	question_type(frm) {
		if (frm.doc.question_type === "Open Ended") {
			frm.set_value("correct_answer", "");
		}
		render_correct_answer_selector(frm);
	},

	answer_options(frm) {
		render_correct_answer_selector(frm);
	},

	correct_answer(frm) {
		render_correct_answer_selector(frm);
	},
});
