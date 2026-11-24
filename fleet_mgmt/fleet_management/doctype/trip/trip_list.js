frappe.listview_settings["Trip"] = {
	add_fields: ["status", "planned_start", "vehicle", "driver"],
	get_indicator(doc) {
		const colors = {
			"Draft": "grey",
			"Pending Approval": "orange",
			"Approved": "blue",
			"In Progress": "cyan",
			"Completed": "green",
			"Rejected": "red",
			"Cancelled": "darkgrey"
		};
		return [__(doc.status), colors[doc.status] || "grey", "status,=," + doc.status];
	}
};
