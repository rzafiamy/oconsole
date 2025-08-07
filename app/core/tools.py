import json

def get_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_linux_command",
                "description": "Generates one or more Linux commands to accomplish a given task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "A clear and concise description of the task the user wants to accomplish. For example, 'list all files in the current directory including hidden ones'."
                        }
                    },
                    "required": ["task_description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "answer_question",
                "description": "Provides a conversational answer to a user's general question or statement.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The user's question or statement. For example, 'what is a kernel?' or 'hello, how are you?'."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

def generate_linux_command(task_description):
    """Placeholder for the logic that generates a command. In our new design, the LLM will generate this."""
    return task_description

def answer_question(query):
    """Placeholder for the logic that answers a question. The LLM provides the answer directly."""
    return query

def format_response(data, schema):
    """
    Formats the final output into the user-specified JSON structure.
    """
    response = {
        "type": "json_object",
        "strict": True,
        "schema": schema,
        "data": data
    }
    return json.dumps(response, indent=2)

# --- Response Schemas ---
# Defines the structure of the data for different tool outputs.

COMMAND_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "commands": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "A valid Linux command."
            },
            "description": "A list of one or more Linux commands to be executed."
        }
    },
    "required": ["commands"]
}

CONVERSATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "response": {
            "type": "string",
            "description": "A conversational response to the user's query."
        }
    },
    "required": ["response"]
}