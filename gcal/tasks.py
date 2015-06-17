from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from datetime import datetime
from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage

def sync_all():
	# get the list of user with 
	users = get_users_by_sync_optios('Hourly')
	# sych the calendar for all frappe users 
	sych_users_calender(users)

def sync_hourly():
	# get the list of user having sync option as "hourly"
	users = get_users_by_sync_optios('Hourly')

def sync_daily():
	# get the list of user having sync option as "Daily"
	users = get_users_by_sync_optios('Daily')

def sync_weekly():
	# get the list of user having sync option as "Weekly"
	users = get_users_by_sync_optios('Weekly')

def sync_monthly():
	# get the list of user having sync option as "Monthly"
	users = get_users_by_sync_optios('Monthly')

def get_users_by_sync_optios(mode):
	return frappe.db.sql("select gmail_id from `tabSync Configuration` where is_sync=1 and sync_options='Hourly'",as_list=True)

def sych_users_calender(users):
	for user in users:
		# get user credentials from keyring storage
		store = Storage('GCal', user[0])
		credentials = store.get()
		if not credentials or credentials.invalid:
			# invalid credentials
			print "invalid credentials", user[0]
		else:
			sync_google_calendar(credentials)

def sync_google_calendar(credentials):
	# get service object
	# get all the events
	events = get_gcal_events(credentials)
	if not events:
		frappe.msgprint("No Events to Sync")
	else:
		for event in events:
			# check if event alreay synced if exist update else create new event
			e_name = is_event_already_exist(event)
			update_event(e_name, event) if e_name else save_event(event)

def get_gcal_events(credentials):
	now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	service = build('calendar', 'v3', http=credentials.authorize(Http()))
	eventsResult = service.events().list(
		calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])

	return events

def save_event(event):
	e = frappe.new_doc("Event")
	e = set_values(e, event)
	e.save(ignore_permissions=True)
	frappe.db.commit()

def update_event(name, event):
	e = frappe.get_doc("Event", name)
	e = set_values(e, event)
	e.save(ignore_permissions=True)
	frappe.db.commit()

def set_values(doc, event):
	doc.subject = event.get('summary')

	start_date = event['start'].get('dateTime', event['start'].get('date'))
	end_date = event['end'].get('dateTime', event['start'].get('date'))

	doc.starts_on = get_formatted_date(start_date)
	doc.ends_on = get_formatted_date(end_date)
	
	doc.all_day = 1 if doc.starts_on == doc.ends_on else 0

	if not event.get('visibility'):
		doc.event_type = "Private"
	else:
		doc.event_type =  "Private" if event['visibility'] == "private" else "Public"

	doc.description = event.get("description")
	doc.is_gcal_event = 1
	doc.event_owner = event.get("organizer").get("email")
	doc.gcal_id = event.get("id")

	return doc

def get_formatted_date(str_date):
	# remove timezone from str_date
	str_date = str_date.split("+")[0]

	date = None
	
	if len(str_date.split("T")) == 1:
		str_date = date_list[0] + "T00:00:00"
	
	date = datetime.strptime(str_date, '%Y-%m-%dT%H:%M:%S').strftime("%d-%m-%Y %H:%M:%S")
	# return datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
	return date

def is_event_already_exist(event):
	name = frappe.db.get_value("Event",{"gcal_id":event.get("id")},"name")
	return name