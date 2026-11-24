# Copyright (c) 2026, test and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestVehicle(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Vehicle")

	def test_vehicle_creation_and_normalisation(self):
		vehicle = frappe.get_doc({
			"doctype": "Vehicle",
			"vehicle_name": " Test Van 1 ",
			"registration_number": " dl-01-ab-1234 ",
			"vehicle_type": "Van",
			"fuel_type": "Diesel",
			"current_odometer": 1000.0,
			"status": "Available",
		}).insert()

		self.assertEqual(vehicle.registration_number, "DL-01-AB-1234")
		self.assertEqual(vehicle.vehicle_name, "Test Van 1")
		self.assertEqual(vehicle.current_odometer, 1000.0)

	def test_negative_odometer_rejected(self):
		vehicle = frappe.get_doc({
			"doctype": "Vehicle",
			"vehicle_name": "Test Truck",
			"registration_number": "MH-02-CD-5678",
			"vehicle_type": "Truck",
			"fuel_type": "Diesel",
			"current_odometer": -50.0,
			"status": "Available",
		})
		self.assertRaises(frappe.ValidationError, vehicle.insert)
