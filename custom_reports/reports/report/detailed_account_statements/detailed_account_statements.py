# Copyright (c) 2023, ahmed ramzi and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub
import erpnext
from datetime import datetime
from frappe.utils import cint, flt, round_based_on_smallest_currency_fraction
import json
from erpnext.controllers.accounts_controller import (
    validate_conversion_rate,
    validate_inclusive_tax,
    validate_taxes_and_charges,
)
from erpnext.stock.get_item_details import _get_item_tax_template
from erpnext.utilities.regional import temporary_flag

from erpnext import get_company_currency, get_default_company

def execute(filters=None):
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    company = get_default_company()
    currency = get_company_currency(company)
    columns = [
         
       {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Link","options":"Doctype", "width": 100},
         {"label": _("Voucher no"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link","options":"voucher_type", "width": 200},
         {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link","options":"Customer", "width": 200},
         {"label": _("Customer Name"), "fieldname": "customer_name", "width": 200},
         {"label": _("Remark"), "fieldname": "remark", "fieldtype": "Data", "width": 230},
         {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Data", "width": 102},
         {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 150},
         {
			"label": _("Debit ({0})").format(currency),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 100,
		},
       {
			"label": _("Credit ({0})").format(currency),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 100,
		},
          {
			"label": _("Balance ({0})").format(currency),
			"fieldname": "balance",
			"fieldtype": "Float",
			"width": 100,
		}
    ]

    return columns

def get_data(filters):
    data = []

    if filters.get("customer"):
        data = get_data_for_customer(filters, filters.get("customer"))
    elif filters.get("customer_group"):
        customers = frappe.get_list("Customer", filters={'customer_group': filters.get("customer_group")})
        for customer in customers:
            temp = get_data_for_customer(filters, customer.name)
            data.extend(temp) 
    return data



def get_data_for_customer(filters , customer):
        balance=0
        sales_filter=set_sales_filters(filters , customer)
        payment_filter=set_payment_filters(filters , customer)

        data = []
        opening_balance=get_opening_balance(customer,filters.get("from_date"))
        opening_debit=0
        opening_credit=0
        field="debit" if opening_balance > 0 else "credit"

        if field == "debit":
            opening_debit+=opening_balance
        else:
            opening_credit+=opening_balance

        balance+=opening_balance
        data.append({"remark":"Opening",field:abs(opening_balance),"balance":balance})

        vouchers=[]

        sales_invoices=frappe.db.get_all("Sales Invoice",filters=sales_filter,fields=["name","is_return","posting_date" , "customer" , "customer_name"])
        
        payment_entries=frappe.db.get_all("Payment Entry",filters=payment_filter,fields=["name","posting_date","paid_amount","party as customer","party_name as customer_name","remarks","payment_type","received_amount"])

        if len(sales_invoices):
            for sales in sales_invoices:
                sales["voucher_type"]="Sales Invoice"
                vouchers.append(sales)

        if len(payment_entries):
            for payment in payment_entries:
                payment["voucher_type"]="Payment Entry"
                payment["type"]="credit"
                vouchers.append(payment)  
        if len(vouchers) :   
            vouchers=arrange_vouchers_dates(vouchers) 
                         
            
            vouchers=get_items_from_vouchers(vouchers)
            total_debit=0
            total_credit=0
            for v in vouchers:
                if "debit" in v:
                    total_debit+=v["debit"] 
                    amount=v["debit"] 
                if "credit" in v:
                    total_credit+=v["credit"]
                    amount=v["credit"]

                balance=update_balance(balance,v["type"],amount)
                v["balance"]=balance
                data.append(v)
            data.append({"remark":"Totals","debit":total_debit+opening_debit,"credit":total_credit+opening_credit,"balance":balance })
            
           
        return data

def get_items_from_vouchers(vouchers):
    
    vouchers_items=[]
    
    for voucher in vouchers:
        if voucher["voucher_type"]=="Payment Entry":
            item_dict={}
            item_dict["voucher_type"]="Payment Entry"
            item_dict["voucher_no"]=voucher["name"]
            item_dict["remark"]=voucher["remarks"]
            item_dict["date"]=voucher["posting_date"]
            item_dict["customer"]=voucher["customer"]
            item_dict["customer_name"]=voucher["customer_name"]
            if voucher["payment_type"]=="Receive":
                item_dict["type"]="credit"
                item_dict["credit"]=voucher["paid_amount"]
            if voucher["payment_type"]=="Pay" :
                item_dict["type"]="debit"
                item_dict["debit"]=voucher["received_amount"]
            
            vouchers_items.append(item_dict)
        
        if  voucher["voucher_type"]=="Sales Invoice":
         
            sales_invoice_items=frappe.db.get_all("Sales Invoice Item",filters={"parent":voucher["name"]},fields=["item_code","qty","uom","net_amount",])
         
            if len(sales_invoice_items):
                tax_amount=frappe.db.get_value("Sales Invoice",voucher["name"],"total_taxes_and_charges")
                for sales_invoice_item in sales_invoice_items:
                    item_dict={}
                    item_dict["date"]=frappe.db.get_value("Sales Invoice",voucher["name"],"posting_date")
                    item_dict["voucher_type"]="Sales Invoice"
                    item_dict["customer"]=voucher["customer"]
                    item_dict["customer_name"]=voucher["customer_name"]
                    item_dict["voucher_no"]=voucher["name"]
                    item_dict["remark"]=frappe.db.get_value("Item",sales_invoice_item["item_code"],"item_name")
                    item_dict["quantity"]=sales_invoice_item["qty"]
                    item_dict["uom"]=sales_invoice_item["uom"]
                    
                    
                    is_return=frappe.db.get_value("Sales Invoice",voucher["name"],"is_return")
                    if is_return:
                        field="credit"
                    else:
                        field="debit" 

                    item_dict["type"]= field
                    item_dict[field]=abs(sales_invoice_item["net_amount"])
                    if tax_amount:
                        item_tax= set_tax_for_items(sales_invoice_item["item_code"],voucher["name"],sales_invoice_item["qty"])
                        if item_tax:
                            
                            item_dict[field]=abs(sales_invoice_item["net_amount"]+item_tax)
                    vouchers_items.append(item_dict)
    return vouchers_items
def update_balance(balance,type,amount):
    if type=="debit":
        balance+=amount
    else:
         balance-=amount 

    return balance       
    
def get_opening_balance(customer,from_date):

    opening_docs = frappe.get_list('GL Entry', filters={"is_cancelled":0,"party":customer,"posting_date":["<",from_date]}, fields=[
        "sum(debit) as debit", "sum(credit) as credit "], order_by='posting_date desc',)[0]

    
    if not opening_docs.get("debit"):
        opening_docs["debit"] = 0

    if not opening_docs.get("credit"):
        opening_docs["credit"] = 0
    balance = opening_docs["debit"] - opening_docs["credit"]
    return balance

def set_tax_for_items(item_code,voucher,item_qty):
    doc=frappe.get_doc("Sales Invoice",voucher)
    tax_breack=get_itemised_tax_breakup(doc)
    qty=0
    for item in doc.items:
        if item.item_code == item_code:
            qty+= item.qty
    if len(tax_breack):
        tax_amount=0
        for tax in tax_breack:
           
            if tax["item"]==item_code:
               
                for k,v in tax.items():
                    if k !="item" and k!="taxable_amount":
                        
                        tax_amount+=v["tax_amount"]
                        
        return (tax_amount/qty)*item_qty
    return None

def arrange_vouchers_dates(vouchers):
    return sorted(vouchers, key=lambda x: x['posting_date'])   

def calc_balance(balance,voucher):
    if voucher["voucher_type"]=="Payment Entry":
        balance=balance-voucher[""]

def set_sales_filters(filters , customer):
    sales_filters = {}
    sales_filters["docstatus"]=1
    if customer:
        sales_filters["customer"] = ["in", customer]

    if filters.get("to_date") and filters.get("from_date"):
        sales_filters["posting_date"] = [
            "between", (filters.get("from_date"), filters.get("to_date"))]    



    return sales_filters
def set_payment_filters(filters , customer):
    payment_filters={}
    payment_filters["docstatus"]=1
    if customer:
        payment_filters["party"] = ["in", customer]
    if filters.get("to_date") and filters.get("from_date"):
        payment_filters["posting_date"] = [
            "between", (filters.get("from_date"), filters.get("to_date"))]    
    return payment_filters


def get_itemised_tax_breakup(doc):
    if not doc.taxes:
        return

    # get headers
    tax_accounts = []
    for tax in doc.taxes:
        if getattr(tax, "category", None) and tax.category == "Valuation":
            continue
        if tax.description not in tax_accounts:
            tax_accounts.append(tax.description)

    with temporary_flag("company", doc.company):
        headers = get_itemised_tax_breakup_header(doc.doctype + " Item", tax_accounts)
        itemised_tax_data = get_itemised_tax_breakup_data(doc)

        return itemised_tax_data
   

@erpnext.allow_regional
def update_itemised_tax_data(doc):
    # Don't delete this method, used for localization
    pass

def get_rounded_tax_amount(itemised_tax, precision):
    # Rounding based on tax_amount precision
    for taxes in itemised_tax:
        for row in taxes.values():
            if isinstance(row, dict) and isinstance(row["tax_amount"], float):
                row["tax_amount"] = flt(row["tax_amount"], precision)

@erpnext.allow_regional
def get_itemised_tax_breakup_header(item_doctype, tax_accounts):
    return [_("Item"), _("Taxable Amount")] + tax_accounts


@erpnext.allow_regional
def get_itemised_tax_breakup_data(doc):
    itemised_tax = get_itemised_tax(doc.taxes)

    itemised_taxable_amount = get_itemised_taxable_amount(doc.items)

    itemised_tax_data = []
    for item_code, taxes in itemised_tax.items():
        itemised_tax_data.append(
            frappe._dict(
                {"item": item_code, "taxable_amount": itemised_taxable_amount.get(item_code), **taxes}
            )
        )

    return itemised_tax_data

def get_itemised_tax(taxes, with_tax_account=False):
    itemised_tax = {}
    for tax in taxes:
        if getattr(tax, "category", None) and tax.category == "Valuation":
            continue

        item_tax_map = json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
        if item_tax_map:
            for item_code, tax_data in item_tax_map.items():
                itemised_tax.setdefault(item_code, frappe._dict())

                tax_rate = 0.0
                tax_amount = 0.0

                if isinstance(tax_data, list):
                    tax_rate = flt(tax_data[0])
                    tax_amount = flt(tax_data[1])
                else:
                    tax_rate = flt(tax_data)

                itemised_tax[item_code][tax.description] = frappe._dict(
                    dict(tax_rate=tax_rate, tax_amount=tax_amount)
                )

                if with_tax_account:
                    itemised_tax[item_code][tax.description].tax_account = tax.account_head

    return itemised_tax

def get_itemised_taxable_amount(items):
    itemised_taxable_amount = frappe._dict()
    for item in items:
        item_code = item.item_code or item.item_name
        itemised_taxable_amount.setdefault(item_code, 0)
        itemised_taxable_amount[item_code] += item.net_amount

    return itemised_taxable_amount