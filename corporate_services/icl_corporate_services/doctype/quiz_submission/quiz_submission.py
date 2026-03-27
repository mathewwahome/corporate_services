# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QuizSubmission(Document):
    def validate(self):
        if self.quiz and not (self.answers or []):
            frappe.throw("Quiz answers must be generated before saving or submitting.")

    def before_submit(self):
        self.calculate_results()

    def calculate_results(self):
        correct = 0
        total = len(self.answers or [])
        gradable_total = 0
        has_pending_review = False

        for row in self.answers or []:
            question = frappe.get_doc("Quiz Question", row.question)
            question_type = question.question_type or "Single Select"
            correct_answers = self._get_correct_answers(question)
            normalized_selected_answers = self._resolve_answers(question, row.selected_answer)
            is_correct = self._is_correct_response(question, row.selected_answer)

            row.question_text = question.question
            row.question_type = question_type
            row.selected_answer = "\n".join(normalized_selected_answers)
            row.correct_answer = "\n".join(correct_answers)

            if is_correct is None:
                row.is_correct = 0
                has_pending_review = True
            else:
                row.is_correct = 1 if is_correct else 0
                gradable_total += 1
                if row.is_correct:
                    correct += 1

        self.total_questions = total
        self.correct_answers = correct
        self.score_ = round((correct / gradable_total) * 100, 2) if gradable_total > 0 else 0

        quiz = frappe.get_doc("Quiz", self.quiz)
        passing_score = quiz.passing_score_ or 70

        if has_pending_review:
            self.passed = 0
            self.result = "Pending Review"
        elif self.score_ >= passing_score:
            self.passed = 1
            self.result = "Pass"
        else:
            self.passed = 0
            self.result = "Fail"

    def _split_values(self, value):
        if not value:
            return []

        text = (value or "").replace("|||", "\n").replace(",", "\n")
        return [part.strip() for part in text.splitlines() if part.strip()]

    def _normalize(self, value):
        return (value or "").strip().lower()

    def _get_defined_options(self, question):
        if (question.answer_options or "").strip():
            return [value.strip() for value in question.answer_options.splitlines() if value.strip()]

        return [
            value.strip()
            for value in (question.option_a, question.option_b, question.option_c, question.option_d)
            if value
        ]

    def _get_option_lookup(self, question):
        lookup = {}

        for index, option in enumerate(self._get_defined_options(question)):
            normalized_option = self._normalize(option)
            lookup[normalized_option] = option
            if index < 26:
                lookup[chr(ord("a") + index)] = option

        return lookup

    def _resolve_answers(self, question, raw_value):
        lookup = self._get_option_lookup(question)
        resolved = []

        for answer in self._split_values(raw_value):
            resolved.append(lookup.get(self._normalize(answer), answer.strip()))

        return resolved

    def _get_correct_answers(self, question):
        return self._resolve_answers(question, question.correct_answer)

    def _is_correct_response(self, question, selected_answer):
        question_type = question.question_type or "Single Select"
        correct_answers = self._get_correct_answers(question)

        if question_type == "Open Ended":
            return None

        if question_type == "Multi Select":
            selected_values = {self._normalize(value) for value in self._resolve_answers(question, selected_answer)}
            correct_values = {self._normalize(value) for value in correct_answers}
            return bool(correct_values) and selected_values == correct_values

        selected_values = self._resolve_answers(question, selected_answer)
        normalized_selected = self._normalize(selected_values[0] if selected_values else "")
        return normalized_selected in {self._normalize(value) for value in correct_answers}
