import frappe


@frappe.whitelist()
def get_my_active_trips():
	"""Get currently dispatched/in-progress trips for the logged-in user or active drivers."""
	user = frappe.session.user
	if user == "Administrator" or "Fleet Manager" in frappe.get_roles(user) or "Fleet Administrator" in frappe.get_roles(user):
		return frappe.get_list(
			"Trip",
			filters={"status": "In Progress"},
			fields=["name", "vehicle", "driver", "origin", "destination", "planned_start", "opening_odometer"],
		)

	# If logged in as driver, filter by driver user mapping if available
	return frappe.get_list(
		"Trip",
		filters={"status": "In Progress"},
		fields=["name", "vehicle", "driver", "origin", "destination", "planned_start", "opening_odometer"],
	)


@frappe.whitelist()
def dispatch_trip(trip_name: str, opening_odometer: float | None = None):
	"""Dispatch an approved trip and update odometer and vehicle status."""
	trip = frappe.get_doc("Trip", trip_name)
	if trip.status != "Approved":
		frappe.throw(f"Trip '{trip_name}' must be Approved before dispatch (current status: {trip.status}).")

	trip.status = "In Progress"
	trip.actual_start = frappe.utils.now_datetime()
	if opening_odometer is not None:
		trip.opening_odometer = float(opening_odometer)
	trip.save()
	return trip


@frappe.whitelist()
def complete_trip(trip_name: str, closing_odometer: float, remarks: str | None = None):
	"""Complete an in-progress trip and reconcile vehicle availability."""
	trip = frappe.get_doc("Trip", trip_name)
	if trip.status != "In Progress":
		frappe.throw(f"Trip '{trip_name}' is not In Progress (current status: {trip.status}).")

	trip.status = "Completed"
	trip.actual_end = frappe.utils.now_datetime()
	trip.closing_odometer = float(closing_odometer)
	if remarks:
		trip.remarks = remarks
	trip.save()
	return trip
