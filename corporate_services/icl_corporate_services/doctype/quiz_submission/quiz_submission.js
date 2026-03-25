// Copyright (c) 2026, IntelliSOFT Consulting and contributors
// For license information, please see license.txt

let quiz_submission_styles_added = false;

function ensure_quiz_submission_styles() {
	if (quiz_submission_styles_added) {
		return;
	}

	const style = document.createElement("style");
	style.textContent = `
		.quiz-test-shell {
			padding: 8px 0 4px;
		}

		.quiz-test-placeholder {
			padding: 24px;
			border: 1px dashed #cbd5e1;
			border-radius: 14px;
			background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
			color: #475569;
		}

		.quiz-test-header {
			margin-bottom: 18px;
			padding: 18px 20px;
			border: 1px solid #dbe4ee;
			border-radius: 14px;
			background: #f8fafc;
		}

		.quiz-test-title {
			margin: 0;
			font-size: 18px;
			font-weight: 700;
			color: #0f172a;
		}

		.quiz-test-meta {
			margin-top: 6px;
			font-size: 13px;
			color: #475569;
		}

		.quiz-question-list {
			display: grid;
			gap: 16px;
		}

		.quiz-question-card {
			border: 1px solid #dbe4ee;
			border-radius: 16px;
			background: #ffffff;
			padding: 20px;
			box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
		}

		.quiz-question-number {
			font-size: 12px;
			font-weight: 700;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			color: #2563eb;
			margin-bottom: 8px;
		}

		.quiz-question-text {
			margin: 0 0 8px;
			font-size: 17px;
			line-height: 1.5;
			font-weight: 600;
			color: #0f172a;
		}

		.quiz-question-type {
			display: inline-flex;
			padding: 4px 10px;
			border-radius: 999px;
			background: #eff6ff;
			color: #1d4ed8;
			font-size: 12px;
			font-weight: 600;
			margin-bottom: 14px;
		}

		.quiz-question-help {
			margin: 0 0 14px;
			color: #475569;
			font-size: 13px;
			line-height: 1.5;
		}

		.quiz-choice-list {
			display: grid;
			gap: 10px;
			margin-bottom: 14px;
		}

		.quiz-choice {
			display: flex;
			align-items: flex-start;
			gap: 10px;
			padding: 12px 14px;
			border: 1px solid #dbe4ee;
			border-radius: 12px;
			background: #f8fafc;
		}

		.quiz-choice input {
			margin-top: 3px;
		}

		.quiz-choice-label {
			flex: 1;
			color: #0f172a;
			line-height: 1.5;
		}

		.quiz-open-response {
			width: 100%;
			min-height: 140px;
			resize: vertical;
			border: 1px solid #cbd5e1;
			border-radius: 12px;
			padding: 14px;
			font-size: 14px;
			line-height: 1.6;
		}

		.quiz-response-note {
			margin-top: 10px;
			font-size: 12px;
			color: #64748b;
		}
	`;

	document.head.appendChild(style);
	quiz_submission_styles_added = true;
}

function escape_html(value) {
	return String(value || "")
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

function split_response_values(value) {
	return (value || "")
		.split(/\r?\n|\|\|\|/)
		.map((item) => item.trim())
		.filter(Boolean);
}

function get_defined_options(question) {
	const answer_options = (question.answer_options || "")
		.split(/\r?\n/)
		.map((value) => value.trim())
		.filter(Boolean);

	if (answer_options.length) {
		return answer_options;
	}

	return [question.option_a, question.option_b, question.option_c, question.option_d]
		.map((value) => (value || "").trim())
		.filter(Boolean);
}

function get_question_help_text(question_type) {
	if (question_type === "Multi Select") {
		return "Select all the answers that apply.";
	}

	if (question_type === "Open Ended") {
		return "Write your answer in the space below. This response will be reviewed manually.";
	}

	return "Select one answer.";
}

async function get_doc(doctype, name) {
	const response = await frappe.call({
		method: "frappe.client.get",
		args: { doctype, name },
	});

	return response.message;
}

async function ensure_question_map(frm) {
	if (frm._quiz_question_map && Object.keys(frm._quiz_question_map).length) {
		return frm._quiz_question_map;
	}

	const question_names = (frm.doc.answers || [])
		.map((row) => row.question)
		.filter(Boolean);

	if (!question_names.length) {
		frm._quiz_question_map = {};
		return frm._quiz_question_map;
	}

	const questions = await Promise.all(
		question_names.map((question_name) => get_doc("Quiz Question", question_name))
	);

	frm._quiz_question_map = {};
	questions.forEach((question) => {
		frm._quiz_question_map[question.name] = question;
	});

	return frm._quiz_question_map;
}

function get_answer_row(frm, question_name) {
	return (frm.doc.answers || []).find((row) => row.question === question_name);
}

function set_row_response(frm, question_name, value) {
	const row = get_answer_row(frm, question_name);
	if (!row) {
		return;
	}

	row.selected_answer = value;
	frm.dirty();
}

function render_choice_question(row, question, disabled) {
	const options = get_defined_options(question);
	const selected_values = split_response_values(row.selected_answer);
	const input_type = row.question_type === "Multi Select" ? "checkbox" : "radio";

	return `
		<div class="quiz-choice-list">
			${options
				.map((option, option_index) => {
					const checked =
						input_type === "checkbox"
							? selected_values.includes(option)
							: row.selected_answer === option;

					return `
						<label class="quiz-choice">
							<input
								type="${input_type}"
								name="quiz-${escape_html(row.question)}"
								data-question="${escape_html(row.question)}"
								data-option="${escape_html(option)}"
								${checked ? "checked" : ""}
								${disabled ? "disabled" : ""}
							/>
							<span class="quiz-choice-label">${escape_html(option)}</span>
						</label>
					`;
				})
				.join("")}
		</div>
	`;
}

function render_open_response(row, disabled) {
	return `
		<textarea
			class="quiz-open-response"
			data-open-question="${escape_html(row.question)}"
			placeholder="Type your answer here"
			${disabled ? "disabled" : ""}
		>${escape_html(row.selected_answer || "")}</textarea>
	`;
}

function render_question_card(row, question, index, disabled) {
	const question_type = row.question_type || "Single Select";
	const help_text = get_question_help_text(question_type);
	const response_ui =
		question_type === "Open Ended"
			? render_open_response(row, disabled)
			: render_choice_question(row, question, disabled);

	const response_note =
		question_type === "Multi Select"
			? `<div class="quiz-response-note">You can select more than one option.</div>`
			: "";

	return `
		<div class="quiz-question-card">
			<div class="quiz-question-number">Question ${index + 1}</div>
			<p class="quiz-question-text">${escape_html(row.question_text)}</p>
			<div class="quiz-question-type">${escape_html(question_type)}</div>
			<p class="quiz-question-help">${escape_html(help_text)}</p>
			${response_ui}
			${response_note}
		</div>
	`;
}

function render_quiz_interface(frm) {
	ensure_quiz_submission_styles();

	const wrapper = frm.fields_dict.quiz_questions_html && frm.fields_dict.quiz_questions_html.$wrapper;
	if (!wrapper) {
		return;
	}

	if (!frm.doc.quiz) {
		wrapper.html(`
			<div class="quiz-test-shell">
				<div class="quiz-test-placeholder">Select a quiz to load its questions here.</div>
			</div>
		`);
		return;
	}

	if (!(frm.doc.answers || []).length) {
		wrapper.html(`
			<div class="quiz-test-shell">
				<div class="quiz-test-placeholder">Loading quiz questions...</div>
			</div>
		`);
		return;
	}

	const disabled = frm.doc.docstatus !== 0;
	const question_cards = (frm.doc.answers || [])
		.map((row, index) => {
			const question = (frm._quiz_question_map && frm._quiz_question_map[row.question]) || {};
			return render_question_card(row, question, index, disabled);
		})
		.join("");

	wrapper.html(`
		<div class="quiz-test-shell">
			<div class="quiz-test-header">
				<h3 class="quiz-test-title">${escape_html(frm.doc.quiz)}</h3>
				<div class="quiz-test-meta">
					${frm.doc.total_questions || (frm.doc.answers || []).length} question(s)
				</div>
			</div>
			<div class="quiz-question-list">${question_cards}</div>
		</div>
	`);

	wrapper.off(".quiz_submission");

	wrapper.on("change.quiz_submission", "input[type='radio'][data-question]", function () {
		const question_name = this.dataset.question;
		const option = this.dataset.option || "";
		set_row_response(frm, question_name, option);
	});

	wrapper.on("change.quiz_submission", "input[type='checkbox'][data-question]", function () {
		const question_name = this.dataset.question;
		const selected = [];

		wrapper
			.find("input[type='checkbox'][data-question]:checked")
			.filter(function () {
				return this.dataset.question === question_name;
			})
			.each(function () {
				selected.push(this.dataset.option || "");
			});

		set_row_response(frm, question_name, selected.join("\n"));
	});

	wrapper.on("input.quiz_submission", "textarea[data-open-question]", function () {
		const question_name = this.dataset.openQuestion;
		set_row_response(frm, question_name, this.value);
	});
}

async function load_quiz_questions(frm) {
	if (!frm.doc.quiz) {
		frm._quiz_question_map = {};
		frm.clear_table("answers");
		frm.set_value("total_questions", 0);
		frm.set_value("correct_answers", 0);
		frm.set_value("score_", 0);
		frm.set_value("passed", 0);
		frm.set_value("result", "");
		frm.refresh_field("answers");
		render_quiz_interface(frm);
		return;
	}

	const existing_answers = {};
	(frm.doc.answers || []).forEach((row) => {
		existing_answers[row.question] = {
			selected_answer: row.selected_answer,
		};
	});

	const quiz = await get_doc("Quiz", frm.doc.quiz);
	const question_names = (quiz.questions || [])
		.map((row) => row.question)
		.filter(Boolean);

	const questions = await Promise.all(
		question_names.map((question_name) => get_doc("Quiz Question", question_name))
	);

	frm._quiz_question_map = {};
	questions.forEach((question) => {
		frm._quiz_question_map[question.name] = question;
	});

	frm.clear_table("answers");

	questions.forEach((question) => {
		const row = frm.add_child("answers");
		const previous_answer = existing_answers[question.name] || {};

		row.question = question.name;
		row.question_text = question.question;
		row.question_type = question.question_type || "Single Select";
		row.answer_options_display = "";
		row.selected_answer = previous_answer.selected_answer || "";
		row.correct_answer = "";
		row.is_correct = 0;
	});

	frm.set_value("total_questions", questions.length);
	frm.set_value("correct_answers", 0);
	frm.set_value("score_", 0);
	frm.set_value("passed", 0);
	frm.set_value("result", "");
	frm.refresh_field("answers");
	render_quiz_interface(frm);
}

function validate_quiz_submission(frm) {
	const missing_questions = (frm.doc.answers || []).filter(
		(row) => !(row.selected_answer || "").trim()
	);

	if (missing_questions.length) {
		const first_missing = missing_questions[0];
		frappe.throw(`Please answer all questions before submitting. Missing: ${first_missing.question_text}`);
	}
}

frappe.ui.form.on("Quiz Submission", {
	async refresh(frm) {
		frm.set_query("quiz", () => ({
			filters: {
				status: "Active",
			},
		}));

		frm.set_df_property("answers", "cannot_add_rows", 1);

		if (frm.doc.quiz && frm.doc.docstatus === 0 && !(frm.doc.answers || []).length) {
			await load_quiz_questions(frm);
			return;
		}

		await ensure_question_map(frm);
		render_quiz_interface(frm);
	},

	async quiz(frm) {
		await load_quiz_questions(frm);
	},

	validate(frm) {
		validate_quiz_submission(frm);
	},
});
