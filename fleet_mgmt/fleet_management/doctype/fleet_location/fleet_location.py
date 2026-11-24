# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FleetLocation(Document):
	def before_naming(self):
		# autoname is "field:location_code", so the name is taken from
		# location_code *before* validate runs, and Frappe then syncs the
		# field back from the name (_sync_autoname_field). Normalise here
		# so the document name itself is upper-case.
		self.normalize_fields()

	def validate(self):
		self.normalize_fields()

	def normalize_fields(self):
		if self.location_code:
			self.location_code = self.location_code.strip().upper()
		if self.location_name:
			self.location_name = self.location_name.strip()
