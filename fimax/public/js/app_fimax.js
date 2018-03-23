// Copyright (c) 2017, Yefri Tavarez and contributors
// For license information, please see license.txt

$(frappe).ready((event) => {
	$.extend(frappe.app, {
		refresh_notifications: function() {
			var me = this;
			if (frappe.session_alive) {
				return frappe.call({
					method: "frappe.desk.notifications.get_notifications",
					args: {	"user": frappe.session.user },
					callback: function callback(r) {
						if (r.message) {
							$.extend(frappe.boot.notification_info, r.message);
							$(document).trigger("notification-update");

							me.update_notification_count_in_modules();

							if (frappe.get_route()[0] != "messages") {
								if (r.message.new_messages.length) {
									frappe.utils.set_title_prefix("(" + r.message.new_messages.length + ")");
								}
							}
						}
					},
					freeze: false,
					type: "GET",
				});
			}
		},

		update_notification_count_in_modules: function() {
			$.each(frappe.boot.notification_info.open_count_doctype, function (doctype, count) {
				if (count) {
					$('.open-notification.global[data-doctype="' + doctype + '"]').removeClass("hide").html(count);
				} else {
					$('.open-notification.global[data-doctype="' + doctype + '"]').addClass("hide");
				}
			});
		},
	});
});

frappe.provide("fimax.utils");

$.extend(fimax.utils, {
	"from_percent_to_decimal": (value) => {
		return flt(value) / flt(100.000);
	},
	"frequency_in_years": (frequency) => {
		return {
			"daily": 365,
			"weekly": 52,
			"biweekly": 26,
			"monthly": 12,
			"quartely": 4,
			"half-yearly": 2,
			"yearly": 1
		}[new String(frequency).toLocaleLowerCase()];
	}
});

