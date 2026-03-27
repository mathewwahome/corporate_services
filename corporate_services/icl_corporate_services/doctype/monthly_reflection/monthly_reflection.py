# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

REVIEW_PERIOD_PATTERN = re.compile(
	r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}$"
)


class MonthlyReflection(Document):
	def validate(self):
		self.validate_review_period()
		self.validate_unique_employee_review_period()

	def validate_review_period(self):
		if not self.review_period:
			return

		if not REVIEW_PERIOD_PATTERN.fullmatch(self.review_period.strip()):
			frappe.throw(
				_(
					"Review Period must be selected in the format 'March 2026'."
				)
			)

	def validate_unique_employee_review_period(self):
		if not self.employee or not self.review_period:
			return

		existing = frappe.db.exists(
			"Monthly Reflection",
			{
				"employee": self.employee,
				"review_period": self.review_period,
				"name": ["!=", self.name],
			},
		)

		if existing:
			frappe.throw(
				_(
					"Employee {0} already has a Monthly Reflection for review period {1}: {2}"
				).format(self.employee, self.review_period, existing)
			)
