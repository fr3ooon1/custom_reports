// Copyright (c) 2024, smart and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Detailed Account Statements"] = {
    "filters": [
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
            // reqd:1
            on_change: function() {
                let customer = frappe.query_report.get_filter_value('customer');
                if (customer) {
                    frappe.query_report.set_filter_value('customer_group', null);
                }
            }
        },
        {
            fieldname: "customer_group",
            label: __("Customer Group"),
            fieldtype: "Link",
            options: "Customer Group",
            // reqd:1
            on_change: function() {
                let customer_group = frappe.query_report.get_filter_value('customer_group');
                if (customer_group) {
                    frappe.query_report.set_filter_value('customer', null);
                }
            }
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
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        return value;
    },
};
