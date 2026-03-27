# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class InternshipCommencement(Document):
	def validate(self):
		self._validate_single_commencement_per_employee()

	def on_submit(self):
		onboarding_schedule = frappe.db.get_value(
			"Onboarding Schedule",
			{"employee": self.intern},
			"name",
			order_by="modified desc",
		)

		if not onboarding_schedule:
			return

		frappe.db.set_value(
			"Onboarding Schedule",
			onboarding_schedule,
			{
				"for_interns_send_internship_commencement_form": 1,
				"internship_commencement": self.name,
			},
			update_modified=True,
		)

	def _validate_single_commencement_per_employee(self):
		if not self.intern:
			return

		existing = frappe.db.exists(
			"Internship Commencement",
			{
				"intern": self.intern,
				"name": ["!=", self.name],
			},
		)

		if existing:
			frappe.throw(
				_("Employee {0} already has an Internship Commencement: {1}").format(
					self.intern, existing
				)
			)
