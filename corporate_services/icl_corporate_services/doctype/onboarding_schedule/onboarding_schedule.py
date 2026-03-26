# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OnboardingSchedule(Document):
	def validate(self):
		self._validate_single_schedule_per_employee()

	def _validate_single_schedule_per_employee(self):
		if not self.employee:
			return

		existing = frappe.db.exists(
			"Onboarding Schedule",
			{
				"employee": self.employee,
				"name": ["!=", self.name],
			},
		)

		if existing:
			frappe.throw(
				_("Employee {0} already has an Onboarding Schedule: {1}").format(
					self.employee, existing
				)
			)
