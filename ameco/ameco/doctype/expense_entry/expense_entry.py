import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from erpnext.accounts.general_ledger import (
    delete_gl_entries,
    make_gl_entries,
    make_reverse_gl_entries,
)
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_fiscal_year


class ExpenseEntry(Document):
    def validate(self):
        self.set_defaults()
        self.validate_amount()
        self.validate_accounts()
        self.calculate_totals()

    def on_submit(self):
        self.make_gl_entries()

    def on_cancel(self):
        self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
        make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

    def on_trash(self):
        # cancelled documents already have reversing entries; remove everything
        # that is still linked to this voucher before the document is deleted
        delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

    def set_defaults(self):
        if not self.company:
            self.company = frappe.defaults.get_user_default("Company")
        if not self.cost_center and self.company:
            self.cost_center = frappe.get_cached_value("Company", self.company, "cost_center")

    def validate_amount(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("Amount must be greater than zero"))
        if flt(self.tax_rate) and not self.tax_account:
            frappe.throw(_("Tax Account is required when Tax Rate is set"))

    def validate_accounts(self):
        company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
        for field in ("expense_account", "paid_through", "tax_account"):
            account = self.get(field)
            if not account:
                continue
            company, currency = frappe.get_cached_value("Account", account, ["company", "account_currency"])
            if company != self.company:
                frappe.throw(_("Account {0} does not belong to company {1}").format(account, self.company))
            if currency and currency != company_currency:
                frappe.throw(_("Account {0} must be in company currency {1}").format(account, company_currency))

    def calculate_totals(self):
        rate = flt(self.tax_rate) if self.tax_account else 0
        amount = flt(self.amount)
        precision = self.precision("amount")

        if self.tax_inclusive == "Tax Inclusive":
            self.total_amount = amount
            self.net_amount = flt(amount / (1 + rate / 100), precision)
            self.tax_amount = flt(amount - self.net_amount, precision)
        else:
            self.net_amount = amount
            self.tax_amount = flt(amount * rate / 100, precision)
            self.total_amount = flt(amount + self.tax_amount, precision)

    def get_gl_entries(self):
        entries = []

        def add(account, debit=0, credit=0, party=None, against=None, against_voucher=False):
            entries.append(
                frappe._dict(
                    account=account,
                    party_type="Supplier" if party else None,
                    party=party,
                    debit=debit,
                    credit=credit,
                    debit_in_account_currency=debit,
                    credit_in_account_currency=credit,
                    against=against,
                    against_voucher_type=self.doctype if against_voucher else None,
                    against_voucher=self.name if against_voucher else None,
                    voucher_type=self.doctype,
                    voucher_no=self.name,
                    posting_date=self.posting_date,
                    company=self.company,
                    cost_center=self.cost_center,
                    fiscal_year=get_fiscal_year(self.posting_date, company=self.company)[0],
                    remarks=self.notes or self.reference_no or _("Expense Entry {0}").format(self.name),
                )
            )

        total = flt(self.total_amount)

        if self.vendor:
            payable = get_party_account("Supplier", self.vendor, self.company)

            # 1. book the expense against the supplier
            add(payable, credit=total, party=self.vendor, against=self.expense_account, against_voucher=True)
            add(self.expense_account, debit=flt(self.net_amount), against=self.vendor)
            if flt(self.tax_amount):
                add(self.tax_account, debit=flt(self.tax_amount), against=self.vendor)

            # 2. settle the supplier from the paid-through account
            add(payable, debit=total, party=self.vendor, against=self.paid_through, against_voucher=True)
            add(self.paid_through, credit=total, against=self.vendor)
        else:
            add(self.expense_account, debit=flt(self.net_amount), against=self.paid_through)
            if flt(self.tax_amount):
                add(self.tax_account, debit=flt(self.tax_amount), against=self.paid_through)
            add(self.paid_through, credit=total, against=self.expense_account)

        return entries

    def make_gl_entries(self):
        make_gl_entries(self.get_gl_entries())
