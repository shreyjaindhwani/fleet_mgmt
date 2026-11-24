# Copyright (c) 2026, test and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMaintenanceRequest(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Maintenance Request")
		frappe.db.delete("Vehicle")

		self.vehicle = frappe.get_doc({
			"doctype": "Vehicle",
			"vehicle_name": "Service Truck",
			"registration_number": "MH-12-AB-9999",
			"vehicle_type": "Truck",
			"fuel_type": "Diesel",
			"current_odometer": 20000.0,
			"status": "Available",
		}).insert()

	def test_maintenance_sets_vehicle_status(self):
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"vehicle": self.vehicle.name,
			"issue_type": "Scheduled Service",
			"description": "50,000 km routine maintenance inspection",
			"priority": "Medium",
			"odometer_reading": 20000.0,
			"status": "Open",
		}).insert()

		veh_status = frappe.db.get_value("Vehicle", self.vehicle.name, "status")
		self.assertEqual(veh_status, "Maintenance")

		# Completion requires resolution notes
		req.status = "Completed"
		req.resolution_notes = ""
		self.assertRaises(frappe.ValidationError, req.save)

		# A failed save has already bumped req.modified in memory, so the next
		# save would hit TimestampMismatchError. Reload, as a user would.
		req.reload()
		req.status = "Completed"
		req.resolution_notes = "Engine oil replaced, brake pads checked."
		req.save()

		veh_status_after = frappe.db.get_value("Vehicle", self.vehicle.name, "status")
		self.assertEqual(veh_status_after, "Available")
