# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _
from frappe.desk.search import sanitize_searchfield
from frappe.utils import (flt, getdate, get_url, now,
	nowtime, get_time, today, get_datetime, add_days)
from frappe.utils import add_to_date, now, nowdate


def on_update_after_submit_1(doc, method=None):
	#frappe.db.commit()
	'''if getdate(doc.new_date) < getdate(doc.end_date):
		frappe.throw(_("New Date cannot be before End Date."))
	'''
	if doc.extend_validity and doc.new_date:
		frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Extended" where name = %s""", doc.name)
		doc.reload()
	if not doc.bank_guarantee_status == "Returned" and not doc.extend_validity and getdate(nowdate()) >= getdate(doc.end_date):
		frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Expired" where name = %s""", doc.name)
		doc.reload()
	if not doc.bank_guarantee_status == "Returned" and doc.extend_validity and getdate(nowdate()) >= getdate(doc.new_date):
		frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Expired" where name = %s""", doc.name)
		doc.reload()
	if not doc.deduction_return and doc.bank_guarantee_purpose == "Deduction":
		frappe.throw(_("Select the Return Account before submitting."))
	bg_return(doc)

def on_submit_1(doc, method=None):
	frappe.db.sql(""" update `tabBank Guarantee` set issued = 1 where name = %s""", doc.name)
	frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Issued" where name = %s""", doc.name)
	if not doc.bank and (doc.bank_guarantee_purpose == "Bank Guarantee" or doc.bank_guarantee_purpose == "Cheque"):
		frappe.throw(_("Select the Bank before submitting."))
	if not doc.bank and (doc.bank_guarantee_purpose == "Bank Guarantee" or doc.bank_guarantee_purpose == "Cheque"):
		frappe.throw(_("Select the Bank Account before submitting."))
	if not doc.rate and doc.bank_guarantee_purpose == "Bank Guarantee":
		frappe.throw(_("Enter the Bank Rate (%) before submitting."))
	if not doc.bank_amount and doc.bank_guarantee_purpose == "Bank Guarantee":
		frappe.throw(_("Enter the Bank Amount before submitting."))
	if not doc.dpaccount and not doc.bank_guarantee_purpose == "Cheque":
		frappe.throw(_("Select the Insurance Account before submitting."))
	if not doc.dpaccountc:
		frappe.throw(_("Select the Fees Account before submitting."))
	if not doc.cash_account and doc.bank_guarantee_purpose == "Cash":
		frappe.throw(_("Select the Cash Account before submitting."))
	if not doc.bank and doc.bank_guarantee_purpose == "Cheque":
		frappe.throw(_("Select the Drawn Bank before submitting."))
	if not doc.dpaccount and doc.bank_guarantee_purpose == "Cheque":
		frappe.throw(_("Select the Insurance Account before submitting."))
	if not doc.reference_date and doc.bank_guarantee_purpose == "Cheque":
		frappe.throw(_("Enter the Reference Date before submitting."))
	if not doc.dpaccount and (doc.bank_guarantee_purpose == "Bank Guarantee" or doc.bank_guarantee_purpose == "Deduction"):
		frappe.throw(_("Select the Insurance Account before submitting."))
	if doc.bank_guarantee_purpose == "Bank Guarantee" and doc.bg_commission <1:
		frappe.throw(_("Bank Guarantee Commission cannot be zero !"))
	frappe.db.sql(""" update `tabBank Guarantee` set posting_date = Null where name = %s""", doc.name)
	frappe.db.commit()
	bg_issue(doc)
	#doc.reload()

def bg_issue(doc, method=None):
	company = frappe.db.get_value("Company", frappe.db.get_value("Global Defaults", None, "default_company"),
								  "company_name")
	if doc.party_type == "Customer":
		party_account = frappe.db.get_value("Company", company, "default_receivable_account")
	else:
		party_account = frappe.db.get_value("Company", company, "default_payable_account")

	if not doc.posting_date:
		frappe.throw(_("Please Enter Posting Date."))
	elif doc.bank_guarantee_purpose == "Deduction" and doc.return_ == "Yes" and doc.issued and not doc.deduction_return:
		frappe.throw(_("Please Select the Return Account."))
	else:
		if doc.bank_guarantee_purpose == "Cash" and not doc.issued and doc.bg_type == "Providing":

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.cash_account,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Issue Cash Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Issue Cash Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_purpose == "Cash" and not doc.issued and doc.bg_type == "Receiving":

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.cash_account,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Issue Cash Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Issue Cash Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_purpose == "Bank Guarantee" and not doc.issued and doc.banking_facilities == "Without Facilities":

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccountc,
					"debit": doc.bg_commission,
					"credit": 0,
					"debit_in_account_currency": doc.bg_commission,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"debit": 0,
					"credit": doc.bg_commission,
					"credit_in_account_currency": doc.bg_commission,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Issue Bank Guarantee Without Facilities  {0}').format(doc.name),
				"total_debit": doc.amount + doc.bg_commission,
				"total_credit": doc.amount + doc.bg_commission,
				"remark": _('Issue Bank Guarantee Without Facilities  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_purpose == "Bank Guarantee" and not doc.issued and doc.banking_facilities == "With Facilities":

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccountc,
					"debit": doc.bg_commission,
					"credit": 0,
					"debit_in_account_currency": doc.bg_commission,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"debit": 0,
					"credit": doc.bank_amount,
					"credit_in_account_currency": doc.bank_amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"debit": 0,
					"credit": doc.bg_commission,
					"credit_in_account_currency": doc.bg_commission,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account_1,
					"debit": 0,
					"credit": doc.facility_amount,
					"credit_in_account_currency": doc.facility_amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Issue Bank Guarantee With Facilities  {0}').format(doc.name),
				"total_debit": doc.amount + doc.bg_commission,
				"total_credit": doc.amount + doc.bg_commission,
				"remark": _('Issue Bank Guarantee With Facilities  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_purpose == "Deduction" and not doc.issued and doc.bg_type == "Providing":

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": party_account,
					"party_type": doc.party_type,
					"party": doc.party,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Issue Deduction Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Issue Deduction Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_purpose == "Deduction" and not doc.issued and doc.bg_type == "Receiving":

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": party_account,
					"party_type": doc.party_type,
					"party": doc.party,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Issue Deduction Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Issue Deduction Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		# Cheques
		if doc.bank_guarantee_purpose == "Cheque" and not doc.issued and doc.bg_type == "Providing":
			company = frappe.db.get_value("Company",
										  frappe.db.get_value("Global Defaults", None, "default_company"),
										  "company_name")
			r_ch_dr = frappe.db.get_value("Company", company, "acc3")
			r_ch_cr = frappe.db.get_value("Company", company, "acc2")
			i_ch_cr = frappe.db.get_value("Company", company, "acc1")
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"credit": 0,
					"debit": doc.amount,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccountc,
					"credit": 0,
					"debit": doc.bg_commission,
					"debit_in_account_currency": doc.bg_commission,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": i_ch_cr,
					"credit": doc.amount,
					"debit": 0,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"credit": doc.bg_commission,
					"debit": 0,
					"credit_in_account_currency": doc.bg_commission,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.reference_date,
				"user_remark": _('Issue Cheque Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Issue Cheque Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_purpose == "Cheque" and not doc.issued and doc.bg_type == "Receiving":
			company = frappe.db.get_value("Company",
										  frappe.db.get_value("Global Defaults", None, "default_company"),
										  "company_name")
			r_ch_dr = frappe.db.get_value("Company", company, "acc3")
			r_ch_cr = frappe.db.get_value("Company", company, "acc2")
			i_ch_cr = frappe.db.get_value("Company", company, "acc1")
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": r_ch_dr,
					"credit": 0,
					"debit": doc.amount,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": r_ch_cr,
					"credit": doc.amount,
					"debit": 0,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.reference_date,
				"user_remark": _('Issue Cheque Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Issue Cheque Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

def bg_return(doc, method=None):
	company =  frappe.db.get_value("Company", frappe.db.get_value("Global Defaults", None, "default_company"), "company_name")
	if doc.party_type == "Customer":
		party_account = frappe.db.get_value("Company", company, "default_receivable_account")
	else:
		party_account = frappe.db.get_value("Company", company, "default_payable_account")
	if not doc.posting_date:
		frappe.throw(_("Please Enter Posting Date."))
	elif doc.bank_guarantee_purpose == "Deduction" and doc.return_ == "Yes" and doc.issued and not doc.deduction_return:
		frappe.throw(_("Please Select the Return Account."))
	else:

		if doc.return_ == "Yes" and doc.bank_guarantee_purpose == "Cash" and not doc.returned and doc.bg_type == "Providing":
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""", doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.cash_account,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Return Cash Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Return Cash Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.return_ == "Yes" and doc.bank_guarantee_purpose == "Cash" and not doc.returned and doc.bg_type == "Receiving":
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.cash_account,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Return Cash Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Return Cash Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		# return BG///////////////////////////////////////////////////
		if doc.return_ == "Yes" and doc.bank_guarantee_purpose == "Bank Guarantee" and not doc.returned and doc.banking_facilities == "Without Facilities":
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()

			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Return Bank Guarantee Without Facilities {0}').format(doc.name),
				"total_debit": doc.amount + doc.bg_commission,
				"total_credit": doc.amount + doc.bg_commission,
				"remark": _('Return Bank Guarantee Without Facilities  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.return_ == "Yes" and doc.bank_guarantee_purpose == "Bank Guarantee" and not doc.returned and doc.banking_facilities == "With Facilities":
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account,
					"debit": doc.bank_amount,
					"credit": 0,
					"debit_in_account_currency": doc.bank_amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.account_1,
					"debit": doc.facility_amount,
					"credit": 0,
					"debit_in_account_currency": doc.facility_amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Return Bank Guarantee With Facilities  {0}').format(doc.name),
				"total_debit": doc.amount + doc.bg_commission,
				"total_credit": doc.amount + doc.bg_commission,
				"remark": _('Return Bank Guarantee With Facilities  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.return_ == "Yes" and doc.bank_guarantee_purpose == "Deduction" and not doc.returned and doc.bg_type == "Providing":
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"party_type": doc.party_type,
					"party": doc.party,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.deduction_return,
					"debit": doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Return Deduction Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Return Deduction Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.return_ == "Yes" and doc.bank_guarantee_purpose == "Deduction" and not doc.returned and doc.bg_type == "Receiving":
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit":  doc.amount,
					"party_type": doc.party_type,
					"party": doc.party,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.deduction_return,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.posting_date,
				"user_remark": _('Return Deduction Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Return Deduction Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_status == "Return" and doc.bank_guarantee_purpose == "Cheque" and not doc.returned and doc.bg_type == "Providing":
			company = frappe.db.get_value("Company",
										  frappe.db.get_value("Global Defaults", None, "default_company"),
										  "company_name")
			r_ch_dr = frappe.db.get_value("Company", company, "acc3")
			r_ch_cr = frappe.db.get_value("Company", company, "acc2")
			i_ch_cr = frappe.db.get_value("Company", company, "acc1")
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": i_ch_cr,
					"debit":  doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": doc.dpaccount,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.reference_date,
				"user_remark": _('Return Cheque Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Return Cheque Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()

		if doc.bank_guarantee_status == "Return" and doc.bank_guarantee_purpose == "Cheque" and not doc.returned and doc.bg_type == "Receiving":
			company = frappe.db.get_value("Company",
										  frappe.db.get_value("Global Defaults", None, "default_company"),
										  "company_name")
			r_ch_dr = frappe.db.get_value("Company", company, "acc3")
			r_ch_cr = frappe.db.get_value("Company", company, "acc2")
			i_ch_cr = frappe.db.get_value("Company", company, "acc1")
			frappe.db.sql(""" update `tabBank Guarantee` set returned = 1 where name = %s""",doc.name)
			frappe.db.sql(""" update `tabBank Guarantee` set bank_guarantee_status = "Returned" where name = %s""",
						  doc.name)
			doc.reload()
			accounts = [
				{
					"doctype": "Journal Entry Account",
					"account": r_ch_cr,
					"debit":  doc.amount,
					"credit": 0,
					"debit_in_account_currency": doc.amount,
					"user_remark": doc.name
				},
				{
					"doctype": "Journal Entry Account",
					"account": r_ch_dr,
					"debit": 0,
					"credit": doc.amount,
					"credit_in_account_currency": doc.amount,
					"user_remark": doc.name
				}
			]
			docs =  frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"reference_doctype": "Bank Guarantee",
				"reference_link": doc.name,
				"company": company,
				"posting_date": doc.posting_date,
				"accounts": accounts,
				"cheque_no": doc.bank_guarantee_number,
				"cheque_date": doc.reference_date,
				"user_remark": _('Return Cheque Bank Guarantee  {0}').format(doc.name),
				"total_debit": doc.amount,
				"total_credit": doc.amount,
				"remark": _('Return Cheque Bank Guarantee  {0}').format(doc.name)

			})
			docs.insert()
			docs.submit()
