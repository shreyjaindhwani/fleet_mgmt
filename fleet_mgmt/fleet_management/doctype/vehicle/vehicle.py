# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class Vehicle(Document):
	def validate(self):
		self.normalize_fields()
		self.validate_odometer()
		self.validate_dates()

	def normalize_fields(self):
		if self.registration_number:
			self.registration_number = self.registration_number.strip().upper()
		if self.vehicle_name:
			self.vehicle_name = self.vehicle_name.strip()

	def validate_odometer(self):
		if self.current_odometer is not None and float(self.current_odometer) < 0:
			frappe.throw("Current Odometer cannot be negative.")

	def validate_dates(self):
		if self.last_service_date and self.next_service_due_date:
			if self.next_service_due_date < self.last_service_date:
				frappe.throw("Next service due date cannot be earlier than last service date.")
