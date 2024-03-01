import json
from datetime import datetime



def lambda_handler(event, context):
    
    raw_body = event['raw_body']

    # Get the current UTC date and time
    current_UTC = datetime.utcnow()
    
    propmt_template = '''Human: You are an helpful assistant that helps human to process the raw content. The raw content is in the <raw_body> section, and it can be in different languages such as English, Norwegian or Chinese. 
Please perform the following tasks for the content:
    1. Create a json object $result as a structured container for storing information. 
    2. Summarize the raw content in English, and store it in json $result.summary field
    3. Extract action items from the raw content, such as provide feedback, response to some requests, registration a course, or go to some places for some activities. Note: it might include multiple action items, and make sure you extract all of them: for example, an invitation include RSVP and the actual event. 
    4. For each action, store its information as an item in an array in $result.actions in following json format:
    [
        "action": {
            "subject": "(the action description)",
            "start_datetime": "(when the action starts)",
            "end_datetime": "(when the action ends)",
            "location": "(where the action takes place)"
        },...
    ]
    Note 1: Do not make up answers. 
    Note 2: Always use UTC for date and time. The current time UTC is {current_UTC}.
    Note 3: If you can not determine the start_date_time or end_date_time of the action, set the missing start_date_time as the noon the day after the current time, and the end time is one hour after start.
    Note 4: If you can not determine location, set it as "N/A"
    5. For each action, call a tool named "create-calendar-reminder" and provide all information from the action as parameter. You may call this tool like this. Only invoke one function at a time and wait for the results before
    invoking another function. Store the all function calls as array in $result.function_calls 
    [
        "function_calls": {
            "tool_name": "create-calendar-reminder",
            "parameters": {
                "body": "(the summary of raw content)",
                "raw_body": "the original raw_body without <raw_body> xml tag",
                (all parameters of the action, for example: subject, start and end date time, location etc. )
            }
        }
    ]
   5. Only output the result_json object, start from  "{" and finish at "}". The result will be parsed as json in programming language, so please do not output any text before and after the result_json block.

<raw_body>
{raw_body}
</raw_body>

Assistant:
    '''
    
    prompt = propmt_template.replace("{raw_body}", raw_body).replace("{current_UTC}", str(current_UTC))
    
    return {
        'statusCode': 200,
        'prompt': prompt
    }