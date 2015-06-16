cur_frm.cscript.sync_calender = function(doc){
	// console.log(doc)
	return frappe.call({
		method:"gcal.gcal_sync.doctype.sync_configuration.sync_configuration.sync_calender",
		callback: function(r){
			if (r.message) {
				window.location.replace(r.message)
			};
		}
	})
}