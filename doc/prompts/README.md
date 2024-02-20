

# Gen AI calendar assistant
A serverless solution that process various inputs such as emails or sms or FB group, extract needed actions (such as attend a dinner, response to a survey, register a course) and mark it on calendar. It is like a human personal assistant that help you to organize calendar items.

# Prerequesit
Setup AWS SES and valid email address. We need that email address for sending emails reminders.

## Step function as backbone
Instead of putting all logics into a monopole application, it uses AWS Step Function to manage the workflow. It is 
easy to extend and can include human interaction (e.g. review LLM output and then take actions). It can do more than Bedrock agent as supporting mutlipe actions and logic/condition/human-interaction

### Workflow
- Get input (SQS or APIGW from gmail webhook)
- Call lambda for generating prompt (pre-reasoning)
- LLM for extract action items in Json (reasoning)
- Step function MAP for looping action item (executing)
-- For each "create reminder item" action, call lambda for sending meeting invitation as reminder


## Incoming data (TODO)
- Gmail (Gmail webhook?)
- SQS/APIGW
- Raw content always is a json 

## LLM ()
- Bedrock Claude v2 
- Max token: 2000?
- Using lambda for generating prompt - easy to manage (than step function built-in). Todo: store prompt template in dynamoDB in the future
- (To-Test) Make sure LLM only return valid json (otherwise maybe XML then extra step convert xml to json, using LLM?)
- LLM generated json is already escaped in step function task, need to convert it to json as part of step function task
- TODO: cannot garantee it generate pure JSON
1) Implement langchain output parser. It can be done in 1) lambda with langchian calling LLM or 2) extra step for processing the result or 3 simply ask step function to retry
---- We might have to convert the native LLM call step function to lambda, in order to handle json result parser. The native LLM call is too simple (that is why we need framework like langchian)
---- 
---- Maybe bedrock agent??? (agent does not work)
### TODO
retry for LLM task

## send reminder lambda

## Google calendar lambda (Not in use)
- Create google project
- create service account and it key file, download its keyfile
- create a shared calendar, note its calendar id
- share the calendar with the service account (important!)
- in lambda function, use the key file and calendar id to create event
- in created event, invite people who need to be informed 
- store the following in secrete manager (export GOOGLE_APPLICATION_CREDENTIALS=./google-key.json)
    - google service account key
    - shared calendar id


