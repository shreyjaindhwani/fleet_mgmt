frappe.listview_settings["Fleet Location"] = {
	add_fields: ["is_active"],
	get_indicator(doc) {
		if (doc.is_active) {
			return [__("Active"), "green", "is_active,=,1"];
		}
		return [__("Inactive"), "grey", "is_active,=,0"];
	}
};
