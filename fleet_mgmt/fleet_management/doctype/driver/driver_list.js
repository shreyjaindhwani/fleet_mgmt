frappe.listview_settings["Driver"] = {
	add_fields: ["status", "license_expiry_date"],
	get_indicator(doc) {
		const colors = {
			"Active": "green",
			"Inactive": "red",
			"Suspended": "orange"
		};
		return [__(doc.status), colors[doc.status] || "grey", "status,=," + doc.status];
	}
};
