import frappe
from num2words import num2words
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import flt


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
        "Request for Quotation": ["items"],
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


def validate_update_stock(self, method=None):
    if self.update_stock or "System Manager" in frappe.get_roles():
        return
    frappe.throw(
        _("Only a System Manager can create a {0} with Update Stock turned off").format(_(self.doctype)),
        title=_("Update Stock Required"),
    )


# (major unit, minor unit) in Arabic
ARABIC_CURRENCIES = {
    "SAR": ("ريال سعودي", "هللة"),
    "AED": ("درهم إماراتي", "فلس"),
    "KWD": ("دينار كويتي", "فلس"),
    "BHD": ("دينار بحريني", "فلس"),
    "OMR": ("ريال عماني", "بيسة"),
    "QAR": ("ريال قطري", "درهم"),
    "EGP": ("جنيه مصري", "قرش"),
    "JOD": ("دينار أردني", "قرش"),
    "USD": ("دولار أمريكي", "سنت"),
    "EUR": ("يورو", "سنت"),
}


def set_arabic_in_words(self, method=None):
    if not self.meta.has_field("custom_in_words_arabic"):
        return

    total = self.grand_total if self.disable_rounded_total else self.rounded_total or self.grand_total
    self.custom_in_words_arabic = amount_in_arabic_words(total, self.currency)


def amount_in_arabic_words(amount, currency=None):
    amount = round(abs(flt(amount)), 2)
    if not amount:
        return ""

    major_name, minor_name = ARABIC_CURRENCIES.get(currency, (currency or "", ""))
    major, minor = divmod(round(amount * 100), 100)

    parts = []
    if major or not minor:
        parts.append(f"{num2words(major, lang='ar')} {major_name}".strip())
    if minor:
        parts.append(f"{num2words(minor, lang='ar')} {minor_name}".strip())

    return "فقط " + " و".join(parts) + " لا غير"


def set_item_code_from_group(self, method=None):
    if self.variant_of:
        return

    prefix = (frappe.db.get_value("Item Group", self.item_group, "custom_item_code_prefix") or "").strip()
    if not prefix:
        frappe.throw(
            _("Please set the Item Code Prefix in Item Group {0} first").format(
                frappe.bold(self.item_group)
            ),
            title=_("Item Code Prefix Missing"),
        )

    self.item_code = make_autoname(f"{prefix}-.#####")
