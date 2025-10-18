def set_accounting_dimensions(self, method=None):
    child_tables = {
        "Purchase Invoice": ["items", "taxes"],
        "Purchase Order": ["items", "taxes"],
        "Sales Invoice": ["items", "taxes"],
        "Sales Order": ["items", "taxes"],
        "Delivery Note": ["items", "taxes"],
        "Payment Entry": ["taxes"],
        "Purchase Receipt": ["items", "taxes"],
        "Journal Entry": ["accounts"],
        "Material Request": ["items"],
        "Quotation": ["items", "taxes"],
        "Supplier Quotation": ["items", "taxes"],
    }

    tables = child_tables.get(self.doctype)
    if not tables:
        return

    for table in tables:
        children = getattr(self, table, [])
        for row in children:
            row.cost_center = self.cost_center
