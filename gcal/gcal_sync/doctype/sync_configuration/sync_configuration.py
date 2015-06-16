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
		social = frappe.get_doc("Social Login Keys", "Social Login Keys")
		keys = {}
		for fieldname in ("client_id", "client_secret"):
			value = social.get("{provider}_{fieldname}".format(provider="google", fieldname=fieldname))
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
		return url
	else:
		from gcal.tasks import sync_google_calendar
		sync_google_calendar(credentials)
		return None

@frappe.whitelist()
def get_credentials(code):
	if code:
		params = get_oauth_keys('gcal')
		params.update({
			"scope": 'https://www.googleapis.com/auth/calendar.readonly',
			"redirect_uri": get_redirect_uri('gcal'),
			"params": {
				"approval_prompt":"force",
				'access_type': 'offline',
				"response_type": "code"
			}
		})
		flow = OAuth2WebServerFlow(**params)
		credentials = flow.step2_exchange(code)
		# Store Credentials in Storage
		store = Storage('GCal', frappe.session.user)
		store.put(credentials)
		# get events and create new doctype
		sync_events(credentials)
	
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/desk#Calendar/Event"

# def sync_events(credentials):
# 	events = get_gcal_events(credentials)
# 	if not events:
# 		frappe.msgprint("No Events to Sync")
# 	else:
# 		for event in events:
# 			# check if event alreay synced if exist update else create new event
# 			e_name = is_event_already_exist(event)
# 			update_event(e_name, event) if e_name else save_event(event)

# def get_gcal_events(credentials):
# 	now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
# 	service = build('calendar', 'v3', http=credentials.authorize(Http()))
# 	eventsResult = service.events().list(
# 		calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
# 		orderBy='startTime').execute()
# 	events = eventsResult.get('items', [])

# 	return events

# def save_event(event):
# 	e = frappe.new_doc("Event")
# 	e = set_values(e, event)
# 	e.save(ignore_permissions=True)
# 	frappe.db.commit()

# def update_event(name, event):
# 	e = frappe.get_doc("Event", name)
# 	e = set_values(e, event)
# 	e.save(ignore_permissions=True)
# 	frappe.db.commit()

# def set_values(doc, event):
# 	doc.subject = event.get('summary')

# 	start_date = event['start'].get('dateTime', event['start'].get('date'))
# 	end_date = event['end'].get('dateTime', event['start'].get('date'))

# 	doc.starts_on = get_formatted_date(start_date)
# 	doc.ends_on = get_formatted_date(end_date)
	
# 	doc.all_day = 1 if doc.starts_on == doc.ends_on else 0

# 	if not event.get('visibility'):
# 		doc.event_type = "Private"
# 	else:
# 		doc.event_type =  "Private" if event['visibility'] == "private" else "Public"

# 	doc.description = event.get("description")
# 	doc.is_gcal_event = 1
# 	doc.event_owner = event.get("organizer").get("email")
# 	doc.gcal_id = event.get("id")

# 	return doc

# def get_formatted_date(str_date):
# 	# Also format the date according to frappe date format
# 	date_list = str_date.split("T")
# 	date = None
	
# 	if len(date_list) == 1:
# 		str_date = date_list[0] + "T00:00:00"
	
# 	date = datetime.strptime(str_date, '%Y-%m-%dT%H:%M:%S').strftime("%d-%m-%Y %H:%M:%S")
# 	# return datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
# 	return date

# def is_event_already_exist(event):
# 	name = frappe.db.get_value("Event",{"gcal_id":event.get("id")},"name")
# 	return name