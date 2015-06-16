# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		"GCal Sync": {
			"color": "blue",
			"icon": "icon-calendar",
			"type": "module",
			"label": _("GCal Sync")
		}
	}
