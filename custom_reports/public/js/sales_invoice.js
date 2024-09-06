frappe.ui.form.on('Sales Invoice', {
    customer: function(frm) {
        if (frm.doc.customer){
            frappe.call({
                method:"custom_reports.api.get_balance",
                args: {
                  party: frm.doc.customer,
                  doctype:"Sales Invoice"
                },
                callback: function (r) {
                  if (r.message) {
                    console.log(r.message);
                    frm.set_value("custom_balance" , r.message);
                    frm.refresh_field("custom_balance");
                  }
                },
              });
        }
    }
});