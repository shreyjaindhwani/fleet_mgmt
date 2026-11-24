# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaintenanceRequest(Document):
	def validate(self):
		self.validate_vehicle()
		self.validate_odometer()
		self.validate_completion()

	def validate_vehicle(self):
		if self.vehicle:
			veh_status = frappe.db.get_value("Vehicle", self.vehicle, "status")
			if veh_status == "Inactive":
				frappe.throw(f"Vehicle '{self.vehicle}' is Inactive and cannot undergo maintenance.")

	def validate_odometer(self):
		if self.odometer_reading is not None:
			if float(self.odometer_reading) < 0:
				frappe.throw("Odometer reading cannot be negative.")
			if self.vehicle:
				current_odo = frappe.db.get_value("Vehicle", self.vehicle, "current_odometer")
				if current_odo and float(self.odometer_reading) < float(current_odo):
					frappe.throw("Odometer reading cannot be less than vehicle's current odometer reading.")

	def validate_completion(self):
		if self.status == "Completed":
			if not self.resolution_notes or not self.resolution_notes.strip():
				frappe.throw("Resolution notes are required on maintenance completion.")

	def on_update(self):
		self.reconcile_vehicle_status()

	def reconcile_vehicle_status(self):
		if not self.vehicle:
			return

		if self.status in ("Open", "In Progress"):
			frappe.db.set_value("Vehicle", self.vehicle, "status", "Maintenance")
			if self.odometer_reading is not None:
				frappe.db.set_value("Vehicle", self.vehicle, "current_odometer", self.odometer_reading)
		elif self.status in ("Completed", "Cancelled"):
			if self.status == "Completed" and self.odometer_reading is not None:
				frappe.db.set_value("Vehicle", self.vehicle, "current_odometer", self.odometer_reading)

			# Check if other maintenance requests are still open
			other_maint = frappe.db.exists(
				"Maintenance Request",
				{
					"vehicle": self.vehicle,
					"status": ["in", ["Open", "In Progress"]],
					"name": ["!=", self.name],
				},
			)
			if other_maint:
				frappe.db.set_value("Vehicle", self.vehicle, "status", "Maintenance")
			else:
				# Check if an active trip is in progress
				active_trip = frappe.db.exists(
					"Trip",
					{
						"vehicle": self.vehicle,
						"status": "In Progress",
					},
				)
				if active_trip:
					frappe.db.set_value("Vehicle", self.vehicle, "status", "On Trip")
				else:
					frappe.db.set_value("Vehicle", self.vehicle, "status", "Available")
