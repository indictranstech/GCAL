# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "gcal"
app_title = "GCal Sync"
app_publisher = "New Indictrans Technologies Pvt Ltd"
app_description = "Sync Google Calender"
app_icon = "icon-calendar"
app_color = "blue"
app_email = "makarand.b@indictranstech.com"
app_version = "0.0.1"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/gcal/css/gcal.css"
# app_include_js = "/assets/gcal/js/gcal.js"

# include js, css files in header of web template
# web_include_css = "/assets/gcal/css/gcal.css"
# web_include_js = "/assets/gcal/js/gcal.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "gcal.install.before_install"
# after_install = "gcal.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "gcal.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Event": {
		"on_update": "gcal.gcal_methods.update_gcal_event",
		"on_trash": "gcal.gcal_methods.delete_gcal_event"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"gcal.gcal_methods.sync_google_events"
	],
	"daily": [
		"gcal.tasks.daily"
	],
	"hourly": [
		"gcal.tasks.hourly"
	],
	"weekly": [
		"gcal.tasks.weekly"
	],
	"monthly": [
		"gcal.tasks.monthly"
	]
}

fixtures = ['Custom Field']

# Testing
# -------

# before_tests = "gcal.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "gcal.event.get_events"
# }

