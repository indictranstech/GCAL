# -*- coding: utf-8 -*-
# Copyright (c) 2015, New Indictrans Technologies Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from datetime import datetime
import os

from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.keyring_storage import Storage

class SyncConfiguration(Document):pass

oauth2_providers = {
	"gcal": {
		"flow_params": {
			"name": "gcal",
			"authorize_url": "https://accounts.google.com/o/oauth2/auth",
			"access_token_url": "https://accounts.google.com/o/oauth2/token",
			"base_url": "https://www.googleapis.com",
		},

		"redirect_uri": "/api/method/gcal.gcal_sync.doctype.sync_configuration.sync_configuration.get_credentials",

		"auth_url_data": {
			# "approval_prompt":"force",
			'access_type': 'offline',
			"scope": 'https://www.googleapis.com/auth/calendar',
			"response_type": "code"
		},

		# relative to base_url
		"api_endpoint": "oauth2/v3/calendar"
	},
}

def get_oauth2_authorize_url(provider):
	flow = get_oauth2_flow(provider)
	# relative to absolute url
	data = { "redirect_uri": get_redirect_uri(provider) }

	# additional data if any
	data.update(oauth2_providers[provider].get("auth_url_data", {}))

	return flow.get_authorize_url(**data)
	# return flow.step1_get_authorize_url(**data)

def get_oauth2_flow(provider):
	from rauth import OAuth2Service

	# get client_id and client_secret
	params = get_oauth_keys(provider)

	# additional params for getting the flow
	params.update(oauth2_providers[provider]["flow_params"])
	# and we have setup the communication lines
	return OAuth2Service(**params)
	# return OAuth2WebServerFlow(client_id=params['client_id'],client_secret=params['client_secret'],scope="https://www.googleapis.com/auth/calendar",redirect_uri=get_redirect_uri('gcal'))

def get_oauth_keys(provider):
	"""get client_id and client_secret from database or conf"""

	# try conf
	keys = frappe.conf.get("{provider}_login".format(provider=provider))

	if not keys:
		# try database
		# social = frappe.get_doc("Social Login Keys", "Social Login Keys")
		social = frappe.get_doc("GCal Secret", "Gcal Secret")
		keys = {}
		for fieldname in ("client_id", "client_secret"):
			value = social.get("{fieldname}".format(fieldname=fieldname))
			if not value:
				keys = {}
				break
			keys[fieldname] = value
	return keys

def get_redirect_uri(provider):
	redirect_uri = oauth2_providers[provider]["redirect_uri"]
	return frappe.utils.get_url(redirect_uri)

@frappe.whitelist()
def sync_calender():
	# check storage for credentials
	store = Storage('GCal', frappe.session.user)
	credentials = store.get()

	if not credentials or credentials.invalid:
		url = get_oauth2_authorize_url('gcal')
		return {
			"url":url,
			"is_synced": False
		}
		# return url
	else:
		from gcal.tasks import sync_google_calendar
		sync_google_calendar(credentials)
		return {
			"url":None,
			"is_synced": True
		}

@frappe.whitelist()
def get_credentials(code):
	if code:
		params = get_oauth_keys('gcal')
		params.update({
			"scope": 'https://www.googleapis.com/auth/calendar',
			"redirect_uri": get_redirect_uri('gcal'),
			"params": {
				"approval_prompt":"force",
				'access_type': 'offline',
				"response_type": "code"
			}
		})
		flow = OAuth2WebServerFlow(**params)
		credentials = flow.step2_exchange(code)
		# Store Credentials in Keyring Storage
		store = Storage('GCal', frappe.session.user)
		store.put(credentials)
		# get events and create new doctype
		from gcal.tasks import sync_google_calendar
		sync_google_calendar(credentials)

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/desk#Calendar/Event"
