# Copyright (c) 2026, test and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestFleetLocation(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Fleet Location")

	def test_location_creation_and_normalisation(self):
		loc = frappe.get_doc({
			"doctype": "Fleet Location",
			"location_name": " Central Depot ",
			"location_code": " depot-01 ",
			"is_active": 1,
		}).insert()

		self.assertEqual(loc.location_code, "DEPOT-01")
		self.assertEqual(loc.location_name, "Central Depot")
		self.assertEqual(loc.is_active, 1)
