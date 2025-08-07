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