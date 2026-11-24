frappe.listview_settings["Maintenance Request"] = {
	add_fields: ["status", "priority", "vehicle"],
	get_indicator(doc) {
		const colors = {
			"Open": "orange",
			"In Progress": "blue",
			"Completed": "green",
			"Cancelled": "grey"
		};
		return [__(doc.status), colors[doc.status] || "grey", "status,=," + doc.status];
	}
};
