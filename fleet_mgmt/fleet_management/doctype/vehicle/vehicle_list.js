frappe.listview_settings["Vehicle"] = {
	add_fields: ["status", "current_odometer", "vehicle_type"],
	get_indicator(doc) {
		const colors = {
			"Available": "green",
			"On Trip": "blue",
			"Maintenance": "orange",
			"Inactive": "red"
		};
		return [__(doc.status), colors[doc.status] || "grey", "status,=," + doc.status];
	}
};
