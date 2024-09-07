frappe.ui.form.on('Purchase Invoice', {
    supplier: function(frm) {
        if (frm.doc.supplier){
            frappe.call({
                method:"custom_reports.api.get_balance",
                args: {
                  party: frm.doc.supplier,
                  doctype:"Purchase Invoice"
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