frappe.ui.form.on("Item", {
    refresh(frm) {
        if (!frm.is_new() || frm.doc.variant_of) return;
        frm.set_df_property("item_code", "reqd", 0);
        frm.set_df_property("item_code", "description", __("Generated from the Item Group's Item Code Prefix on save"));
    },

    item_group(frm) {
        if (!frm.is_new() || !frm.doc.item_group || frm.doc.variant_of) return;
        frappe.db.get_value("Item Group", frm.doc.item_group, "custom_item_code_prefix").then(({ message }) => {
            if (!message || !message.custom_item_code_prefix) {
                frappe.msgprint({
                    title: __("Item Code Prefix Missing"),
                    indicator: "orange",
                    message: __("Please set the Item Code Prefix in Item Group {0} first", [frm.doc.item_group.bold()]),
                });
            }
        });
    },
});
