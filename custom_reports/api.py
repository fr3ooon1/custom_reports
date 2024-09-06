import frappe 
from frappe import _


@frappe.whitelist()
def get_balance(party , doctype):
	invoices = {}
	if doctype == "Sales Invoice":
		invoices = frappe.db.sql(f""" 
								select 
									sum(grand_total) as total 
								from 
						   			`tabSales Invoice` 
						   		where
						   			docstatus = 1 and 
						   			status != 'Paid' and
						   			customer = {party}""" , as_dict = 1)
	elif doctype == "Purchase Invoice":
		invoices = frappe.db.sql(f""" 
						   	select 
								sum(grand_total) as total 
						   	from `tabPurchase Invoice` 
						   	where
						   		docstatus = 1 and
						   		status != 'Paid' and
						   		supplier = {party}""" , as_dict = 1)

	return invoices
	