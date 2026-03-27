# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MonthlyReflectionReminderLog(Document):
	def validate(self):
		self.validate_unique_employee_review_period()

	def validate_unique_employee_review_period(self):
		if not self.employee or not self.review_period:
			return

		existing = frappe.db.exists(
			"Monthly Reflection Reminder Log",
			{
				"employee": self.employee,
				"review_period": self.review_period,
				"name": ["!=", self.name],
			},
		)

		if existing:
			frappe.throw(
				_(
					"Employee {0} already has a Monthly Reflection Reminder Log for review period {1}: {2}"
				).format(self.employee, self.review_period, existing)
			)
