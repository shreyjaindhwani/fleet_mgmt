# Copyright (c) 2026, test and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestDriver(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Driver")

	def test_driver_creation(self):
		driver = frappe.get_doc({
			"doctype": "Driver",
			"driver_name": " John Doe ",
			"employee_id": "EMP-001",
			"license_number": " dl-1420110012345 ",
			"license_expiry_date": add_days(nowdate(), 365),
			"status": "Active",
		}).insert()

		self.assertEqual(driver.driver_name, "John Doe")
		self.assertEqual(driver.license_number, "DL-1420110012345")
		self.assertEqual(driver.status, "Active")
