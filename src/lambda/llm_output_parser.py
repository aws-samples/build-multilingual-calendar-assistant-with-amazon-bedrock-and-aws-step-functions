import json

def parse(input_string):
    start_index = input_string.find('{')  # Find the start of JSON
    end_index = input_string.rfind('}')   # Find the end of JSON
    if start_index == -1 or end_index == -1:
        return None  # If no JSON braces are found, return None

    json_string = input_string[start_index:end_index + 1]  # Extract JSON substring
    try:
        json_data = json.loads(json_string)  # Parse JSON
        return json_data
    except json.JSONDecodeError:
        return None  # Return None if JSON parsing fails

def lambda_handler(event, context):
    completion = event['completion']
    
    parsed_completion = parse(completion)

    return {
        'statusCode': 200,
        'parsed_completion': parsed_completion
    }