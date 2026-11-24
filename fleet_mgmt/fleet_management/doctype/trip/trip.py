# Copyright (c) 2026, test and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, getdate, now_datetime


class Trip(Document):
	def validate(self):
		self.validate_dates()
		self.validate_route()
		self.validate_vehicle_and_driver()
		self.validate_no_overlap()
		self.validate_odometer()
		self.validate_status_requirements()
		self.validate_expenses()

	def validate_dates(self):
		if self.planned_start and self.planned_end:
			if get_datetime(self.planned_end) <= get_datetime(self.planned_start):
				frappe.throw("Planned end must be later than planned start.")

		if self.actual_start and self.actual_end:
			if get_datetime(self.actual_end) < get_datetime(self.actual_start):
				frappe.throw("Actual end must be later than or equal to actual start.")

	def validate_route(self):
		if self.origin and self.destination and self.origin == self.destination:
			frappe.throw("Origin and Destination must differ unless explicitly permitted.")

		if self.origin:
			is_origin_active = frappe.db.get_value("Fleet Location", self.origin, "is_active")
			if is_origin_active is not None and not is_origin_active:
				frappe.throw(f"Origin location '{self.origin}' is inactive.")

		if self.destination:
			is_dest_active = frappe.db.get_value("Fleet Location", self.destination, "is_active")
			if is_dest_active is not None and not is_dest_active:
				frappe.throw(f"Destination location '{self.destination}' is inactive.")

	def validate_vehicle_and_driver(self):
		if self.vehicle:
			vehicle = frappe.get_doc("Vehicle", self.vehicle)
			if self.status in ("In Progress", "Approved") and vehicle.status in ("Inactive", "Maintenance"):
				frappe.throw(f"Vehicle '{self.vehicle}' is not available for dispatch (Status: {vehicle.status}).")

			# Check if vehicle is under active maintenance
			open_maint = frappe.db.exists(
				"Maintenance Request",
				{
					"vehicle": self.vehicle,
					"status": ["in", ["Open", "In Progress"]],
				},
			)
			if open_maint:
				frappe.throw(
					f"Vehicle '{self.vehicle}' is under active maintenance ({open_maint}) and cannot be assigned to a trip."
				)

		if self.driver:
			driver = frappe.get_doc("Driver", self.driver)
			if driver.status != "Active":
				frappe.throw(f"Driver '{self.driver}' is not active (Status: {driver.status}).")

			if driver.license_expiry_date and self.planned_start:
				if getdate(driver.license_expiry_date) < get_datetime(self.planned_start).date():
					frappe.throw(
						f"Driver '{self.driver}' licence is expired or expires before the planned trip start date."
					)

	def validate_no_overlap(self):
		if not self.planned_start or not self.planned_end:
			return

		if self.status == "Cancelled":
			return

		# Check vehicle overlap
		if self.vehicle:
			overlapping_vehicle_trip = frappe.db.sql(
				"""
				SELECT name FROM `tabTrip`
				WHERE vehicle = %(vehicle)s
				  AND name != %(name)s
				  AND status != 'Cancelled'
				  AND planned_start < %(planned_end)s
				  AND planned_end > %(planned_start)s
				LIMIT 1
				""",
				{
					"vehicle": self.vehicle,
					"name": self.name or "",
					"planned_start": self.planned_start,
					"planned_end": self.planned_end,
				},
				as_dict=True,
			)
			if overlapping_vehicle_trip:
				frappe.throw(
					f"Vehicle '{self.vehicle}' already has an overlapping trip: {overlapping_vehicle_trip[0].name}."
				)

		# Check driver overlap
		if self.driver:
			overlapping_driver_trip = frappe.db.sql(
				"""
				SELECT name FROM `tabTrip`
				WHERE driver = %(driver)s
				  AND name != %(name)s
				  AND status != 'Cancelled'
				  AND planned_start < %(planned_end)s
				  AND planned_end > %(planned_start)s
				LIMIT 1
				""",
				{
					"driver": self.driver,
					"name": self.name or "",
					"planned_start": self.planned_start,
					"planned_end": self.planned_end,
				},
				as_dict=True,
			)
			if overlapping_driver_trip:
				frappe.throw(
					f"Driver '{self.driver}' already has an overlapping trip: {overlapping_driver_trip[0].name}."
				)

	def validate_odometer(self):
		if self.opening_odometer is not None and float(self.opening_odometer) < 0:
			frappe.throw("Opening odometer cannot be negative.")

		if self.closing_odometer is not None and float(self.closing_odometer) < 0:
			frappe.throw("Closing odometer cannot be negative.")

		if self.opening_odometer is not None and self.closing_odometer is not None:
			if float(self.closing_odometer) < float(self.opening_odometer):
				frappe.throw("Closing odometer cannot be less than opening odometer.")
			self.distance_travelled = float(self.closing_odometer) - float(self.opening_odometer)

	def validate_status_requirements(self):
		if self.status == "In Progress":
			if not self.actual_start:
				self.actual_start = now_datetime()
			if self.opening_odometer is None and self.vehicle:
				veh_odo = frappe.db.get_value("Vehicle", self.vehicle, "current_odometer")
				self.opening_odometer = float(veh_odo or 0)

		elif self.status == "Completed":
			if not self.actual_start:
				frappe.throw("Actual start datetime is required for a completed trip.")
			if not self.actual_end:
				self.actual_end = now_datetime()
			if self.closing_odometer is None:
				frappe.throw("Closing odometer reading is required for a completed trip.")
			if self.opening_odometer is None:
				frappe.throw("Opening odometer reading is required for a completed trip.")
			self.distance_travelled = float(self.closing_odometer) - float(self.opening_odometer)

	def validate_expenses(self):
		for row in self.get("trip_expenses") or []:
			if row.amount is not None and float(row.amount) < 0:
				frappe.throw("Trip expense amount cannot be negative.")

	def on_update(self):
		self.reconcile_vehicle_status()

	def reconcile_vehicle_status(self):
		if not self.vehicle:
			return

		if self.status == "In Progress":
			frappe.db.set_value("Vehicle", self.vehicle, "status", "On Trip")
		elif self.status in ("Completed", "Cancelled"):
			if self.status == "Completed" and self.closing_odometer is not None:
				frappe.db.set_value("Vehicle", self.vehicle, "current_odometer", self.closing_odometer)

			# Check if there is an active maintenance request
			open_maint = frappe.db.exists(
				"Maintenance Request",
				{
					"vehicle": self.vehicle,
					"status": ["in", ["Open", "In Progress"]],
				},
			)
			if open_maint:
				frappe.db.set_value("Vehicle", self.vehicle, "status", "Maintenance")
			else:
				# Check if any other trip is currently in progress
				other_in_progress = frappe.db.exists(
					"Trip",
					{
						"vehicle": self.vehicle,
						"status": "In Progress",
						"name": ["!=", self.name],
					},
				)
				if other_in_progress:
					frappe.db.set_value("Vehicle", self.vehicle, "status", "On Trip")
				else:
					frappe.db.set_value("Vehicle", self.vehicle, "status", "Available")
