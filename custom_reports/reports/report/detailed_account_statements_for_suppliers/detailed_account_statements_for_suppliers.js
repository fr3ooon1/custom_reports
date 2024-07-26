// Copyright (c) 2024, Muhammad Essam Hassan and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Detailed Account Statements For Suppliers"] = {
	"filters": [
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			reqd:1
	   
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd:1
		},
		{
		  	fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd:1
		},
	],
	tree: true,

  	initial_depth: 3,
  	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		return value;
  },
};
