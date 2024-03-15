import os
import datetime as dt
import uuid
import boto3
import pytz
import icalendar
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dateutil import parser as dt_parser

# If your SES account is still in the sandbox, both from and to address must be verified in SES
sender = os.environ.get('SENDER', 'your_email@domain.com')
recipient = os.environ.get('RECIPIENT', 'your_email@domain.com')

ses_client = boto3.client('ses')

timezone_string = os.environ.get('TIMEZONE', 'Europe/Oslo')
tz = pytz.timezone(timezone_string)

def lambda_handler(event, context):
  #get values from calendar_event
  subject = "[AI Assistant] " + event['subject']
  body = "[AI Assistant found an event and here is the summary]: \n " + event['body']
  raw_body = "[Original message is]: \n " + event['raw_body']
  location = event.get("location", "N/A") #if location does not exist, set it to N/A
  
  #start_datetime = dt.datetime.strptime(event['start_datetime'], '%Y-%m-%dT%H:%M:%SZ')
  #start_datetime = tz.localize(start_datetime)
  start_datetime = dt_parser.parse(event['start_datetime'], ignoretz=True)
  
  #end_datetime = dt.datetime.strptime(event['end_datetime'], '%Y-%m-%dT%H:%M:%SZ')
  #end_datetime = tz.localize(end_datetime)
  end_datetime = dt_parser.parse(event['end_datetime'], ignoretz=True)
   
  # Build the calendar_event itself
  cal = icalendar.Calendar()
  cal.add('prodid', '-//My calendar application//example.com//')
  cal.add('version', '2.0')
  cal.add('method', "REQUEST")
  calendar_event = icalendar.Event()
  calendar_event.add('attendee', recipient)
  calendar_event.add('organizer', sender)
  calendar_event.add('status', "confirmed")
  calendar_event.add('category', "calendar_event")
  calendar_event.add('summary', subject)
  calendar_event.add('location', location)
  calendar_event.add('dtstart', start_datetime)
  calendar_event.add('dtend', end_datetime)
  #calendar_event.add('dtstamp', tz.localize(dt.datetime.combine(mydate, dt.time(6, 0, 0))))
  calendar_event['uid'] = uuid.uuid4() # Generate some unique ID

  calendar_event.add('priority', 5)
  calendar_event.add('sequence', 1)
  calendar_event.add('created', tz.localize(dt.datetime.now()))

  # Add a reminder
  alarm = icalendar.Alarm()
  alarm.add("action", "DISPLAY")
  alarm.add('description', "Reminder")
  # The only way to convince Outlook to do it correctly
  alarm.add("TRIGGER;RELATED=START", "-PT{0}H".format(1))
  calendar_event.add_component(alarm)
  cal.add_component(calendar_event)

  # Build the email message and attach the calendar_event to it
  msg = MIMEMultipart("alternative")

  msg["Subject"] = subject
  msg["From"] = sender
  msg["To"] = recipient
  msg["Content-class"] = "urn:content-classes:calendarmessage"

  # Set message body
  msg_body = body + "\n\n" + raw_body
  msg.attach(MIMEText(msg_body, "plain"))

  filename = "invite.ics"
  part = MIMEBase('text', "calendar", method="REQUEST", name=filename)
  part.set_payload( cal.to_ical() )
  encoders.encode_base64(part)
  part.add_header('Content-Description', filename)
  part.add_header("Content-class", "urn:content-classes:calendarmessage")
  part.add_header("Filename", filename)
  part.add_header("Path", filename)
  msg.attach(part)

  # Convert message to string and send
  response = ses_client.send_raw_email(
      Source=sender,
      Destinations=[recipient],
      RawMessage={"Data": msg.as_string()}
  )

if __name__ == "__main__":
  
  # In order to run this locally, setup the following environment variables:
  # export SENDER=your_email@domain.com
  # export RECIPIENT=your_email@domain.com
  
  data = {
    "subject": "event subject",
    "raw_body": "event raw body",
    "body": "event body",
    "start_datetime": "2024-03-16T09:00:00Z",
    "end_datetime": "2024-01-16T09:15:00Z",
    "location": "myhome",
  } 
  
  context = {}
  lambda_handler(data, context)