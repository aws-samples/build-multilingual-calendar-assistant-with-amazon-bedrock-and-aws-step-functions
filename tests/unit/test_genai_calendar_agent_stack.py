import aws_cdk as core
import aws_cdk.assertions as assertions

from genai_calendar_agent.genai_calendar_agent_stack import GenaiCalendarAgentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in genai_calendar_agent/genai_calendar_agent_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GenaiCalendarAgentStack(app, "genai-calendar-agent")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
