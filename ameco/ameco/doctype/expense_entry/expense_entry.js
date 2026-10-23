frappe.ui.form.on("Expense Entry", {
    setup(frm) {
        frm.set_query("expense_account", () => ({
            filters: { company: frm.doc.company, is_group: 0, account_type: "Expense" },
        }));
        frm.set_query("paid_through", () => ({
            filters: { company: frm.doc.company, is_group: 0, account_type: ["in", ["Bank", "Cash"]] },
        }));
        frm.set_query("tax_account", () => ({
            filters: { company: frm.doc.company, is_group: 0, account_type: "Tax" },
        }));
    },

    company(frm) {
        if (!frm.doc.company) return;
        frappe.db.get_value("Company", frm.doc.company, "cost_center").then(({ message }) => {
            frm.set_value("cost_center", message && message.cost_center);
        });
    },

    refresh(frm) {
        if (frm.doc.docstatus > 0) {
            frm.add_custom_button(
                __("Accounting Ledger"),
                () => frappe.set_route("query-report", "General Ledger", {
                    voucher_no: frm.doc.name,
                    from_date: frm.doc.posting_date,
                    to_date: frm.doc.posting_date,
                    company: frm.doc.company,
                    group_by: "Group by Voucher (Consolidated)",
                }),
                __("View")
            );
        }
    },

    amount: calculate,
    tax_rate(frm) {
        if (!flt(frm.doc.tax_rate)) {
            frm.set_value({ tax_account: "", tax_inclusive: "" });
        }
        calculate(frm);
    },
    tax_inclusive: calculate,
});

function calculate(frm) {
    const amount = flt(frm.doc.amount);
    const rate = flt(frm.doc.tax_rate);
    let net, tax, total;
    if (!rate) {
        net = amount;
        tax = 0;
        total = amount;
    } else if (frm.doc.tax_inclusive === "Tax Inclusive") {
        total = amount;
        net = amount / (1 + rate / 100);
        tax = amount - net;
    } else {
        net = amount;
        tax = (amount * rate) / 100;
        total = amount + tax;
    }
    frm.set_value({ net_amount: net, tax_amount: tax, total_amount: total });
}
