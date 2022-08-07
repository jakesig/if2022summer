# -*- coding: utf-8 -*-

# Imports 

import logging
import ask_sdk_core.utils as ask_utils
import boto3

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Connect to SQS

f = open("keys.txt", "r")
keys = f.read().split(",")
sqs = boto3.resource('sqs', region_name="us-east-1", aws_secret_access_key=str(keys[0]), aws_access_key_id=str(keys[1]))
queue = sqs.get_queue_by_name(QueueName = 'dispense-queue')

# Array of names

names = []

# Launch Request - Triggers when the user says something like "Alexa, launch Sink Mate".

class LaunchRequestHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to sink mate!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# Dispense Intent - Triggers when user asks Sink Mate to dispense water.

class DispenseIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("DispenseIntent")(handler_input)

    # Obtains unit and amount from designated slots, then dispenses water.

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        
        # Obtain values from slots
        
        name = str(slots["name"].value)
        if name == "None":
            name = "none"
        else:
            names.append(name)
        amount = str(slots["amount"].value)
        if amount == "None":
            amount = "0"
        unit = str(slots["unit"].value)
        if unit == "None":
            unit = "none"
            
        speak_output = "Dispensing " + amount + " " + unit + " of water."
        amount = float(amount)
        
        # Determines if the name of the preset exists
        
        exists = False
        for item in names:
            if item == name:
                exists = True
        
        # Exit function if the preset doesn't exist
        
        if not exists and amount == "0" and unit == "none":
            return (
            handler_input.response_builder
                .speak("That preset doesn't exist.")
                .response
        )
        
        # Downsize string if it's plural
        
        if unit.endswith("s"):
            unit = unit[0:len(unit)-1]
        
        # Send message to SQS
        
        queue.send_message(MessageBody='Dispense', MessageAttributes={
            'Name': {
                'StringValue': name,
                'DataType': 'String'
            },
            'Amount': {
                'StringValue': str(amount),
                'DataType': 'Number'
            },
            'Unit': {
                'StringValue': unit,
                'DataType': 'String'
            }
        })
        
        # Speak output
        
        if not exists and amount != "0" and unit != "none":
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .response
            )
        
        speak_output = "Dispensing for your preset ,,," + name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

# Open Intent - Triggers when user wants to enable passthrough mode.

class OpenIntentHandler(AbstractRequestHandler):
    
    def can_handle(self ,handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("OpenIntent")(handler_input)
        
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Enabling passthrough mode."
        
        queue.send_message(MessageBody='PassOn', MessageAttributes={
            'Name': {
                'StringValue': 'none',
                'DataType': 'String'
            },
            'Amount': {
                'StringValue': '0',
                'DataType': 'Number'
            },
            'Unit': {
                'StringValue': "none",
                'DataType': 'String'
            }
        })
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
            )

# Close Intent - Triggers when user wants to disable passthrough mode.
    
class CloseIntentHandler(AbstractRequestHandler):
    
    def can_handle(self ,handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CloseIntent")(handler_input)
        
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Disabling passthrough mode."
        
        queue.send_message(MessageBody='PassOff', MessageAttributes={
            'Name': {
                'StringValue': 'none',
                'DataType': 'String'
            },
            'Amount': {
                'StringValue': '0',
                'DataType': 'Number'
            },
            'Unit': {
                'StringValue': 'none',
                'DataType': 'String'
            }
        })
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
            )

# Preset Intent - Triggers when user wants to set a preset.

class PresetIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PresetIntent")(handler_input)

    # Obtains name, unit, and amount from designated slots, then sets the preset.

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        name = slots["name"].value
        amount = slots["amount"].value
        unit = slots["unit"].value
        speak_output ="Setting " + name + " to " + amount + " " + unit + "."
        
        # Downsize string if it's plural
        
        if unit.endswith("s"):
            unit = unit[0:len(unit)-1]
        
        # Send message to SQS
        
        queue.send_message(MessageBody='Preset', MessageAttributes={
            'Name': {
                'StringValue': name,
                'DataType': 'String'
            },
            'Amount': {
                'StringValue': str(amount),
                'DataType': 'Number'
            },
            'Unit': {
                'StringValue': unit,
                'DataType': 'String'
            }
        })
        
        # Speak output

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


# Help Intent - Triggers when user asks Sink Mate for help.

class HelpIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Ask me to dispense water! Say something like,,, Alexa, dispense six cups of water."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# Cancel or Stop Intent - Triggers when user ends connection to Sink Mate.

class CancelOrStopIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Thanks for using Sink Mate!"
        
        queue.send_message(MessageBody='PassOff', MessageAttributes={
            'Name': {
                'StringValue': 'none',
                'DataType': 'String'
            },
            'Amount': {
                'StringValue': '0',
                'DataType': 'Number'
            },
            'Unit': {
                'StringValue': "none",
                'DataType': 'String'
            }
        })

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

# Runs when connection to Sink Mate ends.

class SessionEndedRequestHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response

# Helpful for seeing if I'm able to trigger a certain intent.

class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

# Catches exceptions.

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(DispenseIntentHandler())
sb.add_request_handler(OpenIntentHandler())
sb.add_request_handler(CloseIntentHandler())
sb.add_request_handler(PresetIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()