// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch('bank_account','account','account');
cur_frm.add_fetch('company','acc1','acc1');
cur_frm.add_fetch('company','acc2','acc2');
cur_frm.add_fetch('company','acc3','acc3');

/////////////////// below scripts are from client script

frappe.ui.form.on("Bank Guarantee", {
	setup: function(frm) {
		frm.set_query("reference_doctype", function() {
			return {
				filters: [
					["DocType", "name", "in", ["Sales Order","Purchase Order"]]
				]
			};
		});
		frm.set_query("dpaccount", function() {
			return {
				filters: [
					["Account", "is_group", "!=", "1"]
				]
			};
		});
		frm.set_query("dpaccountc", function() {
			return {
				filters: [
					["Account", "is_group", "!=", "1"]
				]
			};
		});
		frm.set_query("deduction_return", function() {
			return {
				filters: [
					["Account", "is_group", "!=", "1"]
				]
			};
		});
		frm.set_query("cash_account", function() {
			return {
				filters: [
					["Account", "is_group", "!=", "1"]
				]
			};
		});
	}
});
frappe.ui.form.on("Bank Guarantee", "rate", function(frm) {
     if(cur_frm.doc.banking_facilities == "With Facilities"){
        var x = (frm.doc.rate/100) * frm.doc.amount;
        var y = (100-frm.doc.rate);
        var z = (y/100) * frm.doc.amount;
        cur_frm.set_value("bank_amount", x);
        cur_frm.set_value("rate2", y);
        cur_frm.set_value("facility_amount", z);
     }
});
frappe.ui.form.on("Bank Guarantee", "rate2", function(frm) {
     if(cur_frm.doc.banking_facilities == "With Facilities"){
        frm.doc.rate = (100-frm.doc.rate2);
        frm.doc.bank_amount = (frm.doc.rate/100) * frm.doc.amount;

        frm.doc.facility_amount = (frm.doc.rate2/100) * frm.doc.amount;
     }
});
frappe.ui.form.on("Bank Guarantee", "amount", function(frm) {
    if(cur_frm.doc.banking_facilities == "Without Facilities"){
         cur_frm.set_value("rate", "100");
         cur_frm.set_value("bank_amount", frm.doc.amount);
    }
});

frappe.ui.form.on("Bank Guarantee", "party", function(frm, cdt, cdn) {
    cur_frm.set_value("name_of_beneficiary", cur_frm.doc.party);
});

frappe.ui.form.on("Bank Guarantee", "party", function(frm, cdt, cdn) {
    if (cur_frm.doc.party_type == "Customer"){
        cur_frm.set_value("customer", cur_frm.doc.party);
    }
});



frappe.ui.form.on("Bank Guarantee", {
	setup: function(frm) {
		frm.set_query("cash_account", function() {
			return {
				filters: [
					["Account","account_type", "in", "Cash"]
				]
			};
		});
	}
});

frappe.ui.form.on("Bank Guarantee", {
	setup: function(frm) {
		frm.set_query("deduction_return", function() {
			return {
				filters: [
					["Account","account_type", "in", ["Cash","Bank"]]
				]
			};
		});
	}
});

frappe.ui.form.on("Bank Guarantee", {
	setup: function(frm) {
		frm.set_query("party_type", function() {
			return {
				filters: [
					["DocType", "name", "in", ["Customer","Supplier"]]
				]
			};
		});
	}
});

frappe.ui.form.on("Bank Guarantee", {
	setup: function(frm) {
		frm.set_query("account_for_bank_facilities", function() {
			return {
				filters: [
					["Bank Account","bank", "in", frm.doc.bank]
				]
			};
		});
	}
});

frappe.ui.form.on("Bank Guarantee", "bank_guarantee_purpose", function(frm) {
    if(cur_frm.doc.bank_guarantee_purpose == "Secretariats"){
        cur_frm.set_value("bg_type", "Providing");
    }
});


//frappe.ui.form.on("Bank Guarantee", "end_date", function(frm) {
//   cur_frm.set_value("validity", frappe.datetime.get_day_diff( cur_frm.doc.end_date , cur_frm.doc.start_date ));
// });
frappe.ui.form.on("Bank Guarantee", "rate", function(frm) {
     if(cur_frm.doc.banking_facilities == "With Facilities"){
        var x = (frm.doc.rate/100) * frm.doc.amount;
        var y = (100-frm.doc.rate);
        var z = (y/100) * frm.doc.amount;
        cur_frm.set_value("bank_amount", x);
        cur_frm.set_value("rate2", y);
        cur_frm.set_value("facility_amount", z);
     }
});
frappe.ui.form.on("Bank Guarantee", "rate2", function(frm) {
     if(cur_frm.doc.banking_facilities == "With Facilities"){
        frm.doc.rate = (100-frm.doc.rate2);
        frm.doc.bank_amount = (frm.doc.rate/100) * frm.doc.amount;

        frm.doc.facility_amount = (frm.doc.rate2/100) * frm.doc.amount;
     }
});
frappe.ui.form.on("Bank Guarantee", "amount", function(frm) {
    if(cur_frm.doc.banking_facilities == "Without Facilities"){
         cur_frm.set_value("rate", "100");
         cur_frm.set_value("bank_amount", frm.doc.amount);
    }
});

frappe.ui.form.on("Bank Guarantee", "customer", function(frm, cdt, cdn) {
    cur_frm.set_value("name_of_beneficiary", cur_frm.doc.customer);
});

//frappe.ui.form.on("Bank Guarantee", "end_date", function(frm) {
//   cur_frm.set_value("validity", frappe.datetime.get_day_diff( cur_frm.doc.end_date , cur_frm.doc.start_date ));
// });

frappe.ui.form.on('Process Order', {


///start return functions
bank_guarantee_status: function(frm) {
		if(frm.doc.issued){
			frappe.call({
				doc: frm.doc,
				method: "get_process_details",
				callback: function(r) {
					refresh_field("outputs");
					refresh_field("scrap");
					refresh_field("materials");
				}
			});
		}
	}

})

