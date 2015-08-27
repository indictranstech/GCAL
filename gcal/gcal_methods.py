from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime

from apiclient.discovery import build
from httplib2 import Http
import oauth2client
from oauth2client.client import Credentials
from oauth2client.keyring_storage import Storage
from gcal.gcal_sync.doctype.sync_configuration.sync_configuration import sync_calender

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
		if not (doc.modified == doc.creation):
			event = get_google_event_dict(doc)
			event = service.events().update(calendarId='primary', eventId=doc.gcal_id, body=event).execute()

			if event: frappe.msgprint("Google Calender Event is updated successfully")
	else:
		# create new google calender event
		event = get_google_event_dict(doc)
		event = service.events().insert(calendarId='primary', body=event).execute()

		if event:
			doc.is_gcal_event = 1
			doc.gcal_id = event.get("id")
			frappe.msgprint("New Google Calender Event is created successfully")

def delete_gcal_event(doc, method):
	service = get_service_object()
	if doc.is_gcal_event and doc.gcal_id:
		try:
			service.events().delete(calendarId='primary', eventId=doc.gcal_id).execute()
			frappe.msgprint("New Google Calender Event is deleted successfully")
		except Exception, e:
			frappe.msgprint("Error occured while deleting google event\nDeleting Event from Frappe, Please delete the google event manually")
			frappe.delete_doc("Event", doc.name)
		finally:
			# redirect to event list
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/desk#List/Event"

def get_google_event_dict(doc):
	import json
	start_date, end_date = get_gcal_date(doc.starts_on, doc.ends_on, doc.all_day)
	event = {
		"summary": doc.subject,
		"location": None,
		"description": doc.description,
		"start": start_date,
		"end": end_date,
		"recurrence":get_recurrence_rule(doc) if doc.repeat_this_event else [],
		"attendees": get_attendees(doc),
		"reminders":{
			'useDefault':False,
			'overrides': [
				{'method': 'email','minutes':24 * 60}
			]
		}
	}
	return event

def get_gcal_date(starts_on, ends_on=None, is_all_day=0):
	gcal_date = {}
	gcal_starts_on = get_formatted_date(starts_on, is_all_day)
	gcal_ends_on = get_formatted_date(ends_on if ends_on else starts_on, is_all_day)

	return gcal_starts_on, gcal_ends_on

def get_formatted_date(date, is_all_day=0):
	str_date = str(date) if isinstance(date, datetime) else date
	if is_all_day:
		return {'date': datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")}
	else:
		timezone = frappe.db.get_value("Sync Configuration",frappe.session.user, "time_zone")
		if not timezone:
			timezone = frappe.db.get_value("System Settings", None, "time_zone")
			if timezone:
				return {
					'dateTime':datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S"),
					'timeZone': timezone
				}
			else:
				frappe.msgprint("Please set Time Zone under Setup > Settings > System Settings", raise_exception=1)

def get_attendees(doc):
	import json
	email_ids = []
	if doc.roles:
		roles, attendees = [], []

		for doc in doc.roles:
			if doc.role:
				roles.append(str(doc.role))
			if doc.attendees:
				attendees.extend(eval(doc.attendees))

		if roles:
			condition = "('%s')" % "','".join(tuple(roles))

			result_set = frappe.db.sql("""SELECT DISTINCT email FROM tabUser WHERE name <> '%s' AND name IN
				(SELECT DISTINCT parent FROM tabUserRole WHERE role in %s)"""%(frappe.session.user, condition), as_dict=True)

			email_ids = result_set if result_set else []

		if attendees:
			email_ids.extend(attendees)

	return email_ids

def get_recurrence_rule(doc):
	"""Recurring Event not implemeted."""
	# until = datetime.strptime(doc.repeat_till, '%Y-%m-%d').strftime("%Y%m%dT%H%M%SZ")

	# if doc.repeat_on == "Every Day": return ["RRULE:FREQ=DAILY;UNTIL=%s;BYDAY=%s"%(until,get_by_day_string(doc))]
	# elif doc.repeat_on == "Every Week": return ["RRULE:FREQ=WEEKLY;UNTIL=%s"%(until)]
	# elif doc.repeat_on == "Every Month": return ["RRULE:FREQ=MONTHLY;UNTIL=%s"%(until)]
	# else: return ["RRULE:FREQ=YEARLY;UNTIL=%s"%(until)]
	return []

# def get_by_day_string(doc):
# 	# days = ["SU","MO","TU","WE","TH","FR","SA"]
# 	by_days = []
# 	if doc.sunday : by_days.append("SU")
# 	if doc.monday : by_days.append("MO")
# 	if doc.tuesday : by_days.append("TU")
# 	if doc.wednesday : by_days.append("WE")
# 	if doc.thursday : by_days.append("TH")
# 	if doc.friday : by_days.append("FR")
# 	if doc.saturday : by_days.append("SA")

# 	return "%s" % ",".join(by_days)
