# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=get_data(filters,columns)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Bank Guarantee"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Bank Guarantee",
			"width": 80
		},
		{
			"label": _("No"),
			"fieldname": "bank_guarantee_number",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"label": _("Beneficiary"),
			"fieldname": "name_of_beneficiary",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("purpose"),
			"fieldname": "bank_guarantee_purpose",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Bank"),
			"fieldname": "bank",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Extend Date"),
			"fieldname": "new_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldname": "bank_guarantee_status",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Bank %"),
			"fieldname": "bank_percent",
			"fieldtype": "Percent",
			"width": 80
		},
		{
			"label": _("Bank Amount"),
			"fieldname": "bank_amount",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Facility %"),
			"fieldname": "facility_percent",
			"fieldtype": "Percent",
			"width": 80
		},
		{
			"label": _("Facility Amount"),
			"fieldname": "facility_amount",
			"fieldtype": "Currency",
			"width": 100
		}
	]

def get_data(filters, columns):
	item_price_qty_data = []
	item_price_qty_data = get_item_price_qty_data(filters)
	return item_price_qty_data

def get_item_price_qty_data(filters):
	conditions = ""
	if filters.get("type_of_letter_of_guarantee"):
		conditions += " and a.type_of_letter_of_guarantee=%(type_of_letter_of_guarantee)s"
	if filters.get("status_of_letter_of_guarantee"):
		conditions += " and a.status_of_letter_of_guarantee=%(status_of_letter_of_guarantee)s"
	if filters.get("bank_guarantee_purpose"):
		conditions += " and a.bank_guarantee_purpose=%(bank_guarantee_purpose)s"
	if filters.get("from_date"):
		conditions += " and a.start_date>=%(from_date)s"
	if filters.get("to_date"):
		conditions += " and a.end_date<=%(to_date)s"
	if filters.get("bg_type"):
		conditions += " and a.bg_type=%(bg_type)s"
	if filters.get("bank"):
		conditions += " and a.bank=%(bank)s"
	item_results = frappe.db.sql("""
				select
						a.name as name,
						a.bank_guarantee_number as bank_guarantee_number,
						a.name_of_beneficiary as name_of_beneficiary,
						a.bank_guarantee_purpose as bank_guarantee_purpose,
						a.bank as bank,
						a.bank_guarantee_status as bank_guarantee_status,
						a.end_date as end_date,
						a.start_date as start_date,
						a.new_date as new_date,
						a.amount as amount,
						a.rate as bank_percent,
						a.bank_amount as bank_amount,
						a.rate as facility_percent,
						a.facility_amount as facility_amount						
						from `tabBank Guarantee` a 
				where
					 a.docstatus !=2
					{conditions}
				""".format(conditions=conditions), filters, as_dict=1)


	#price_list_names = list(set([item.price_list_name for item in item_results]))

	#buying_price_map = get_price_map(price_list_names, buying=1)
	#selling_price_map = get_price_map(price_list_names, selling=1)

	result = []
	if item_results:
		for item_dict in item_results:
			data = {
				'name': item_dict.name,
				'bank_guarantee_number': item_dict.bank_guarantee_number,
				'name_of_beneficiary': item_dict.name_of_beneficiary,
				'bank_guarantee_purpose': item_dict.bank_guarantee_purpose,
				'bank': item_dict.bank,
				'bank_guarantee_status': item_dict.bank_guarantee_status,
				'end_date': item_dict.end_date,
				'start_date': item_dict.start_date,
				'new_date': item_dict.new_date,
				'amount': item_dict.amount,
				'bank_percent': item_dict.bank_percent,
				'bank_amount': item_dict.bank_amount,
				'facility_percent': item_dict.facility_percent,
				'facility_amount': item_dict.facility_amount

			}
			result.append(data)

	return result

def get_price_map(price_list_names, buying=0, selling=0):
	price_map = {}

	if not price_list_names:
		return price_map

	rate_key = "Buying Rate" if buying else "Selling Rate"
	price_list_key = "Buying Price List" if buying else "Selling Price List"

	filters = {"name": ("in", price_list_names)}
	if buying:
		filters["buying"] = 1
	else:
		filters["selling"] = 1

	pricing_details = frappe.get_all("Item Price",
		fields = ["name", "price_list", "price_list_rate"], filters=filters)

	for d in pricing_details:
		name = d["name"]
		price_map[name] = {
			price_list_key :d["price_list"],
			rate_key :d["price_list_rate"]
		}

	return price_map