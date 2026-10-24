# import frappe
# from frappe.model import naming
# from frappe.utils import getdate

# DOCTYPES = {
#     "Journal Entry",
#     "Sales Invoice",
#     "Purchase Invoice",
#     "Expense Entry",
#     "Payment Entry",
# }

# _original_parse_naming_series = naming.parse_naming_series


# def parse_naming_series(parts, doc=None, *args, **kwargs):
#     """Resolve the YYYY part of a naming series from the posting date instead of today."""
#     if doc is not None and getattr(doc, "doctype", None) in DOCTYPES and doc.get("posting_date"):
#         year = str(getdate(doc.posting_date).year)
#         if isinstance(parts, str):
#             parts = ".".join(year if p == "YYYY" else p for p in parts.split("."))
#         else:
#             parts = [year if p == "YYYY" else p for p in parts]

#     return _original_parse_naming_series(parts, doc, *args, **kwargs)


# def apply_patch():
#     if naming.parse_naming_series is not parse_naming_series:
#         naming.parse_naming_series = parse_naming_series
