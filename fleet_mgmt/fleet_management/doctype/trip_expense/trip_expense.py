# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TripExpense(Document):
	def validate(self):
		if self.amount is not None and float(self.amount) < 0:
			frappe.throw("Expense amount cannot be negative.")
