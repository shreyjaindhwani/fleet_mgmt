# Copyright (c) 2026, test and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_to_date, now_datetime, nowdate


class TestTrip(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Trip Expense")
		frappe.db.delete("Trip")
		frappe.db.delete("Vehicle")
		frappe.db.delete("Driver")
		frappe.db.delete("Fleet Location")

		self.loc1 = frappe.get_doc({
			"doctype": "Fleet Location",
			"location_name": "Depot",
			"location_code": "DEPOT",
			"is_active": 1,
		}).insert()

		self.loc2 = frappe.get_doc({
			"doctype": "Fleet Location",
			"location_name": "Customer Site A",
			"location_code": "SITE-A",
			"is_active": 1,
		}).insert()

		self.vehicle = frappe.get_doc({
			"doctype": "Vehicle",
			"vehicle_name": "Delivery Van 1",
			"registration_number": "KA-01-EQ-1234",
			"vehicle_type": "Van",
			"fuel_type": "Diesel",
			"current_odometer": 5000.0,
			"status": "Available",
		}).insert()

		self.driver = frappe.get_doc({
			"doctype": "Driver",
			"driver_name": "Alice Smith",
			"employee_id": "EMP-101",
			"license_number": "KA-1420180001",
			"license_expiry_date": add_days(nowdate(), 180),
			"status": "Active",
		}).insert()

	def test_trip_validation_dates(self):
		now = now_datetime()
		# End before start
		trip = frappe.get_doc({
			"doctype": "Trip",
			"vehicle": self.vehicle.name,
			"driver": self.driver.name,
			"origin": self.loc1.name,
			"destination": self.loc2.name,
			"planned_start": now,
			"planned_end": add_to_date(now, hours=-2),
		})
		self.assertRaises(frappe.ValidationError, trip.insert)

	def test_trip_same_origin_and_destination(self):
		now = now_datetime()
		trip = frappe.get_doc({
			"doctype": "Trip",
			"vehicle": self.vehicle.name,
			"driver": self.driver.name,
			"origin": self.loc1.name,
			"destination": self.loc1.name,
			"planned_start": now,
			"planned_end": add_to_date(now, hours=4),
		})
		self.assertRaises(frappe.ValidationError, trip.insert)

	def test_trip_odometer_calculation(self):
		now = now_datetime()
		trip = frappe.get_doc({
			"doctype": "Trip",
			"vehicle": self.vehicle.name,
			"driver": self.driver.name,
			"origin": self.loc1.name,
			"destination": self.loc2.name,
			"planned_start": now,
			"planned_end": add_to_date(now, hours=4),
			"actual_start": now,
			"actual_end": add_to_date(now, hours=3),
			"opening_odometer": 5000.0,
			"closing_odometer": 5120.0,
			"status": "Completed",
		}).insert()

		self.assertEqual(trip.distance_travelled, 120.0)
		# Verify vehicle odometer was updated
		veh_odo = frappe.db.get_value("Vehicle", self.vehicle.name, "current_odometer")
		self.assertEqual(veh_odo, 5120.0)
