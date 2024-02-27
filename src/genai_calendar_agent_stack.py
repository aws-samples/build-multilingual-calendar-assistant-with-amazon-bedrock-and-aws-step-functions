import json
import aws_cdk as core
from aws_cdk import (
    Duration,
    Stack,
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

        prompt_generator_function = lambda_.Function(
            self, "prompt_generator", 
            code=lambda_.Code.from_asset("./src/lambda"),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="prompt_generator.lambda_handler"
        )
        
        llm_output_parser_function = lambda_.Function(
            self, "llm_output_parser",
            code=lambda_.Code.from_asset("./src/lambda"),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="llm_output_parser.lambda_handler"
        )
        
        send_calendar_reminder_function = lambda_.Function(
            self,"send_calendar_reminder",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="send_calendar_reminder.lambda_handler",
            environment={
                "SENDER": "lufng@amazon.com",
                "RECIPIENT": "lufng@amazon.com",
                "TIMEZONE": "Europe/Oslo"
            },
            code=lambda_.Code.from_asset(
                "./src/lambda",
                bundling=core.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache icalendar -t /asset-output && cp -au . /asset-output" #install needed pip package
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
        get_raw_content_job = sfn.Pass(
            self, "get_content_body"
        )
        
        generate_prompt_job = tasks.LambdaInvoke(
            self, "generate_prompt_job",
            lambda_function=prompt_generator_function,
            input_path="$.body", # as we are getting input from api gateway
            result_selector={
                "prompt": sfn.JsonPath.string_at("$.Payload.prompt")
            }
        )


        model = bedrock.FoundationModel.from_foundation_model_id(self, "Model", bedrock.FoundationModelIdentifier.ANTHROPIC_CLAUDE_V2)
        bedrock_extract_event_job = tasks.BedrockInvokeModel(self, "llm_extract_events_job",
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
            self, "parse_llm_output_job",
            lambda_function=llm_output_parser_function,
            result_selector={
                "parsed_completion": sfn.JsonPath.string_at("$.Payload.parsed_completion")
            }
        )
        
        # Map all extracted events and send email reminders
        individual_reminder_map_job_container = sfn.Map(self, "individual_reminder_job_parallel_executor",
            max_concurrency=1,
            items_path=sfn.JsonPath.string_at("$.parsed_completion.result_json.function_calls")
        )
        
        pre_processing_placeholder_job = sfn.Pass(
            self, "pre_processing_placeholder_job"
        )
        
        send_email_job = tasks.LambdaInvoke(
            self, "send_email_job",
            lambda_function=send_calendar_reminder_function, 
            input_path="$.invoke.parameters"
        )
        
        item_processor_chain = pre_processing_placeholder_job.next(send_email_job)
        individual_reminder_map_job_container.item_processor(item_processor_chain)
        
        chain = get_raw_content_job.next(generate_prompt_job).next(bedrock_extract_event_job).next(parse_llm_output_job).next(individual_reminder_map_job_container).next(sfn.Succeed(self, "Done"))
        
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
