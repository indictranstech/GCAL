from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime

from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage

def get_service_object():
	# get google credentials from storage
	service = None
	store = Storage('GCal', frappe.session.user)
	credentials = store.get()

	if not credentials or credentials.invalid:
		# get credentials
		frappe.throw("Invalid Credentials")
	else:
		service = build('calendar', 'v3', http=credentials.authorize(Http()))

	return service

def update_gcal_event(doc, method):
	# check if event newly created or updated
	event = None
	service = get_service_object()

	if doc.is_gcal_event and doc.gcal_id:
		# update google calender event
		event = get_google_event_dict(doc)
		event = service.events().update(calendarId='primary', eventId=doc.gcal_id, body=event).execute()
		if event: frappe.msgprint("Google Calender Event is updated successfully") 
	else:
		# create new google calender event
		event = get_google_event_dict(doc)
		event = service.events().insert(calendarId='primary', body=event).execute()

		if event:
			doc.is_gcal_event = 1
			doc.event_owner = event.get("organizer").get("email")
			doc.gcal_id = event.get("id")

			frappe.msgprint("New Google Calender Event is created successfully") 

def delete_gcal_event(doc, method):
	service = get_service_object()
	if doc.is_gcal_event and doc.gcal_id:
		service.events().delete(calendarId='primary', eventId=doc.gcal_id).execute()
		frappe.msgprint("New Google Calender Event is deleted successfully")

		# redirect to event list
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/desk#List/Event"

def get_google_event_dict(doc):
	event = {
		'kind':'Frappe#event',
		'summary': doc.subject,
		'location': None,
		'description': doc.description,
		'start': get_gcal_date('start', doc),
		'end': get_gcal_date('end', doc),
		'recurrence':get_recurrence_rule(doc) if doc.repeat_this_event else [],
		'attendees': get_attendees(),
		'reminders':{
			'useDefault':False,
			'overrides': [
				{'method': 'email','minutes':24 * 60}
			]
		}
	}
	return event

def get_gcal_date(param, doc):
	# ref 2015-06-22T11:00:00+05:30
	# adjust date or dateTime param
	gcal_date = {}
	date = doc.starts_on if param == 'start' else doc.ends_on
	
	if date:
		gcal_date.update(get_formatted_date(date))
	else:
		if param == "end": gcal_date.update(get_formatted_date(doc.starts_on))

	return gcal_date

def get_formatted_date(date):
	str_date = str(date) if isinstance(date, datetime) else date
	if str_date.split(' ')[1] == "00:00:00":
		return {'date': datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")}
	else:
		# set timezone
		return {'dateTime':datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"}

def get_attendees():
	return []

def get_recurrence_rule(doc):
	# frappe.errprint("in get_recurrence_rule")
	# recur_rule = [
	# 	'DTSTART;'+ get_gcal_date('start',doc),
	# 	'DTEND';+ get_gcal_date('end',doc),
	# 	'PRULE:FREQ='+ get_prule(doc) + ""
	# ]
	# return recur_rule
	return []

def get_repeat_on(doc):
	repeat_on = doc.repeat_on

	if repeat_on == "Every Day": return "DAILY"
	elif repeat_on == "Every Week": return "WEEKLY"
	elif repeat_on == "Every Month": return "MONTHY"
	else: return "YEARLY"

# # # Sync Google Calendar Events to Frappe Event

# def sync_google_events():
# 	print "in sync_google_events"
# 	service = get_service_object()
