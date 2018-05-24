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
	},
	"view_doc": (doc) => {
		frappe.set_route("Form", doc.doctype, doc.name);
	}
});

_f.Frm.prototype._save = function (save_action, callback, btn, on_error, resolve) {
	var _this2 = this;

	var me = this;
	if (!save_action) save_action = "Save";
	this.validate_form_action(save_action, resolve);

	if ((!this.meta.in_dialog || this.in_form) && !this.meta.istable) {
		frappe.utils.scroll_to(0);
	}
	var after_save = function after_save(r) {
		if (!r.exc) {
			if (["Save", "Update", "Amend"].indexOf(save_action) !== -1) {
				frappe.utils.play_sound("click");
			}

			me.script_manager.trigger("after_save");
			// me.refresh();
			me.reload_doc();
		} else {
			if (on_error) {
				on_error();
			}
		}
		callback && callback(r);
		resolve();
	};

	var fail = function fail() {
		btn && $(btn).prop("disabled", false);
		if (on_error) {
			on_error();
		}
		resolve();
	};

	if (save_action != "Update") {
		frappe.validated = true;
		frappe.run_serially([function () {
			return _this2.script_manager.trigger("validate");
		}, function () {
			return _this2.script_manager.trigger("before_save");
		}, function () {
			if (!frappe.validated) {
				fail();
				return;
			}

			frappe.ui.form.save(me, save_action, after_save, btn);
		}]).catch(fail);
	} else {
		frappe.ui.form.save(me, save_action, after_save, btn);
	}
};

_f.Frm.prototype.set_indicator_formatter = function(fieldname, get_color, get_text) {
	var doctype;
	if (frappe.meta.docfield_map[this.doctype][fieldname]) {
		doctype = this.doctype;
	} else {
		frappe.meta.get_table_fields(this.doctype).every(function(df) {
			if (frappe.meta.docfield_map[df.options][fieldname]) {
				doctype = df.options;
				return false;
			} else {
				return true;
			}
		});
	}

	// frappe.meta.docfield_map[doctype][fieldname].formatter = function(value, df, options, doc) {
	frappe.meta.get_docfield(doctype, fieldname, this.doc.name).formatter = function(value, df, options, doc) {
		if (value) {
			return repl('<a class="indicator %(color)s" href="#Form/%(doctype)s/%(name)s">%(label)s</a>', {
				color: get_color(doc || {}),
				doctype: df.options,
				name: value,
				label: get_text ? get_text(doc) : value
			});
		} else {
			return '';
		}
	};
}