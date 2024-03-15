import json
import aws_cdk as core
from aws_cdk import (
    Duration,
    Stack,
    CfnParameter,
    aws_iam as iam,
    aws_logs as logs,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_bedrock as bedrock,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks

)
from constructs import Construct

class GenaiCalendarAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        sender_email = CfnParameter(self, 
                        "senderEmail", 
                        type="String", 
                        description="The sender email address.",
                        default="undefined" # Set default to undefined
                    )
        
        recipient_email = CfnParameter(self, 
                        "recipientEmail", 
                        type="String", 
                        description="The recipient email address.",
                        default="undefined" # Set default to undefined
                    )

        prompt_generator_function = lambda_.Function(
            self, "prompt_generator", 
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="prompt_generator.lambda_handler",
            code=lambda_.Code.from_asset("./src/lambda/prompt_generator")
        )
        
        llm_output_parser_function = lambda_.Function(
            self, "llm_output_parser",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="llm_output_parser.lambda_handler",
            code=lambda_.Code.from_asset(
                "./src/lambda/llm_output_parser"
            ),
        )
        
        send_calendar_reminder_function = lambda_.Function(
            self,"send_calendar_reminder",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="send_calendar_reminder.lambda_handler",
            environment={
                "SENDER": sender_email.value_as_string,
                "RECIPIENT": recipient_email.value_as_string,
                "TIMEZONE": "Europe/Oslo"
            },
            code=lambda_.Code.from_asset(
                "./src/lambda/send_calendar_reminder",
                bundling=core.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output" #install needed pip package
                    ],
                ),
            ),
        )

        send_calendar_reminder_function.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        send_calendar_reminder_function.role.add_to_policy(
            iam.PolicyStatement(
                actions=["ses:SendRawEmail"],
                resources=["*"]
            )
        )
        
        
        # Define step function individual tasks
        generate_prompt_job = tasks.LambdaInvoke(
            self, "generate_prompt",
            lambda_function=prompt_generator_function,
            input_path="$.body", # as we are getting input from api gateway
            result_selector={
                "prompt": sfn.JsonPath.string_at("$.Payload.prompt")
            }
        )


        model = bedrock.FoundationModel.from_foundation_model_id(self, "Model", bedrock.FoundationModelIdentifier.ANTHROPIC_CLAUDE_V2)
        bedrock_extract_event_job = tasks.BedrockInvokeModel(self, "llm_extract_events",
            model=model,
            body=sfn.TaskInput.from_object({
                "prompt.$": "$.prompt",
                "max_tokens_to_sample": 5000
            }),
            result_selector={
                "completion.$": "$.Body.completion"
            }
        )
        
        # a simple retry in case LLM did not return a valid json, try it again will most likely fix that
        bedrock_extract_event_job.add_retry(
            interval=Duration.seconds(5), 
            max_attempts=5,
            max_delay=Duration.seconds(10)
        )
                
        parse_llm_output_job = tasks.LambdaInvoke(
            self, "parse_llm_output",
            lambda_function=llm_output_parser_function,
            result_selector={
                "parsed_completion": sfn.JsonPath.string_at("$.Payload.parsed_completion")
            }
        )
        
        # For each extracted event, process them with its own logic 
        individual_event_map_job_container = sfn.Map(self, "individual_event_processor",
            max_concurrency=1,
            items_path=sfn.JsonPath.string_at("$.parsed_completion.function_calls")
        )
        
        choice_job_selector = sfn.Choice(self, "job_selector")
        
        job_selector_condition = sfn.Condition.string_equals("$.tool_name", "create-calendar-reminder")
        
        other_job_placeholder = sfn.Pass(
            self, "other_job_placeholder"
        )
        
        send_reminder_job = tasks.LambdaInvoke(
            self, "send_reminder_job",
            lambda_function=send_calendar_reminder_function, 
            input_path="$.parameters"
        )
        
        item_processor_chain = choice_job_selector.when(job_selector_condition, send_reminder_job).otherwise(other_job_placeholder).afterwards().next(sfn.Succeed(self, "Success"))
        
        individual_event_map_job_container.item_processor(item_processor_chain)
        
        chain = generate_prompt_job.next(bedrock_extract_event_job).next(parse_llm_output_job).next(individual_event_map_job_container)
        
        log_group = logs.LogGroup(self, "GenAI-Calendar-Assistant-StepFunction-LogGroup")
        
        state_machine = sfn.StateMachine(
            self, "GenAI-Calendar-Assistant",
            state_machine_type=sfn.StateMachineType.EXPRESS,
            definition_body=sfn.DefinitionBody.from_chainable(chain),
            logs=sfn.LogOptions(
                 destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            )
        )
        
        apigw = apigateway.StepFunctionsRestApi(self, 
                    "GenAI-Calendar-Assistant-APIGW",
                    state_machine = state_machine)
        
        core.CfnOutput(self, "APIUrl", value=apigw.url)
