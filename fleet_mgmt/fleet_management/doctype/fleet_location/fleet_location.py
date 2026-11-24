# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FleetLocation(Document):
	def validate(self):
		self.normalize_fields()

	def normalize_fields(self):
		if self.location_code:
			self.location_code = self.location_code.strip().upper()
		if self.location_name:
			self.location_name = self.location_name.strip()
