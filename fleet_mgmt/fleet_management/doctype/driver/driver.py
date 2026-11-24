# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Driver(Document):
	def validate(self):
		self.normalize_fields()

	def normalize_fields(self):
		if self.driver_name:
			self.driver_name = self.driver_name.strip()
		if self.employee_id:
			self.employee_id = self.employee_id.strip()
		if self.license_number:
			self.license_number = self.license_number.strip().upper()
