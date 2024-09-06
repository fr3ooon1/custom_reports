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
						   			customer = '{party}'""" , as_dict = 1)
	elif doctype == "Purchase Invoice":
		invoices = frappe.db.sql(f""" 
						   	select 
								sum(grand_total) as total 
						   	from 
						   		`tabPurchase Invoice` 
						   	where
						   		docstatus = 1 and
						   		supplier = '{party}'""" , as_dict = 1)

	total_balance = balance(party)
	result = float(total_balance or 0) - float(invoices[0].get('outstanding_amount') if invoices else 0)
	return result

def balance(party):
	total_receive = frappe.db.sql(f"""
				select 
						  sum(paid_amount)
						from
						  `tabPayment Entry
						where 
						  docstatus = 1 and
						  payment_type = 'Receive'
						  party = '{party}'

				""",as_dict=1)
	total_pay = frappe.db.sql(f"""
				select 
						  sum(paid_amount)
						from
						  `tabPayment Entry
						where 
						  docstatus = 1 and
						  payment_type = 'Pay'
						  party = '{party}'

				""",as_dict=1)
	
	total = float(total_receive[0].get("paid_amount") if total_receive else 0) - float(total_pay[0].get("paid_amount") if total_pay else 0)
	return total
	