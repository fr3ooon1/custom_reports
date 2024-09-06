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
						  sum(paid_amount) as total_receive
						from
						  `tabPayment Entry`
						where 
						  docstatus = 1 and
						  payment_type = 'Receive' and
						  party = '{party}'

				""",as_dict=1)
	total_pay = frappe.db.sql(f"""
				select 
						  sum(paid_amount) as total_pay
						from
						  `tabPayment Entry`
						where 
						  docstatus = 1 and
						  payment_type = 'Pay' and
						  party = '{party}'

				""",as_dict=1)
	
	total_receive = total_receive[0].get('total_receive') if total_receive and total_receive[0].get('total_receive') is not None else 0
	total_pay = total_pay[0].get('total_pay') if total_pay and total_pay[0].get('total_pay') is not None else 0

	# Calculate the balance
	total = float(total_receive) - float(total_pay)
	return total
	