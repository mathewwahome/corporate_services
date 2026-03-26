# Copyright (c) 2026, IntelliSOFT Consulting and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HRConfig(Document):
	def validate(self):
		self.validate_monthly_reflection_reminder_day()
		self.validate_monthly_reflection_overdue_weekday()

	def validate_monthly_reflection_reminder_day(self):
		if not self.enable_monthly_reflection_reminder:
			return

		day = frappe.utils.cint(self.monthly_reflection_reminder_day)
		if day < 1 or day > 7:
			frappe.throw(
				_("Monthly Reflection Reminder Day must be between 1 and 7.")
			)

	def validate_monthly_reflection_overdue_weekday(self):
		if not self.enable_monthly_reflection_overdue_reminder:
			return

		allowed = {
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		}

		if self.monthly_reflection_overdue_weekday not in allowed:
			frappe.throw(
				_("Please select a valid Monthly Reflection Overdue Reminder Weekday.")
			)
