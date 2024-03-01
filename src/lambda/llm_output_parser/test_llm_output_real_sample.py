import pytest
import llm_output_parser
import json

sample = """
{
"summary": "The raw content is an invitation to attend the soft opening celebration of a store called Honey and Lemon Food and Drink on Jan. 20 at 11.00 at main street 123, NY. It requests attendees to RSVP by Wed to confirm attendance.",
"actions": [
{
"subject": "RSVP to the invitation",
"start_datetime": "2024-03-06T12:00:00Z", 
"end_datetime": "2024-03-06T13:00:00Z",
"location": "N/A"
},
{
"subject": "Attend the soft opening celebration of Honey and Lemon Food and Drink",
"start_datetime": "2024-01-20T11:00:00Z",
"end_datetime": "2024-01-20T12:00:00Z", 
"location": "main street 123, NY"
}
],
"function_calls": [
{
"tool_name": "create-calendar-reminder",
"parameters": {
"body": "The raw content is an invitation to attend the soft opening celebration of a store called Honey and Lemon Food and Drink on Jan. 20 at 11.00 at main street 123, NY. It requests attendees to RSVP by Wed to confirm attendance.", 
"raw_body": "Please join us as we celebrate our store's soft opening on Jan. 20 at 11.00 at main street 123, NY. We've been working hard to open the doors of Honey and Lemon Food and Drink, and we want to invite our most generous supporters for a special night before our grand opening. We plan to provide light snacks and drinks. Please RSVP to confirm your attendance by Wed.",
"subject": "RSVP to the invitation",
"start_datetime": "2024-03-06T12:00:00Z",
"end_datetime": "2024-03-06T13:00:00Z",
"location": "N/A" 
}
},
{
"tool_name": "create-calendar-reminder",
"parameters": {
"body": "The raw content is an invitation to attend the soft opening celebration of a store called Honey and Lemon Food and Drink on Jan. 20 at 11.00 at main street 123, NY. It requests attendees to RSVP by Wed to confirm attendance.",
"raw_body": "Please join us as we celebrate our store's soft opening on Jan. 20 at 11.00 at main street 123, NY. We've been working hard to open the doors of Honey and Lemon Food and Drink, and we want to invite our most generous supporters for a special night before our grand opening. We plan to provide light snacks and drinks. Please RSVP to confirm your attendance by Wed.",
"subject": "Attend the soft opening celebration of Honey and Lemon Food and Drink",
"start_datetime": "2024-01-20T11:00:00Z", 
"end_datetime": "2024-01-20T12:00:00Z",
"location": "main street 123, NY"
}
}
]
}
"""

def test_parse_returns_json_1():
 
   input_string = sample

   result = llm_output_parser.test_parse(input_string)
  

   #assert isinstance(result, dict)
   
   

   
if __name__ == "__main__":
    test_parse_returns_json_1()
