# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


HISTORY_FILE = 'command_history.txt'
PROVIDER = os.getenv('PROVIDER')  # Set the provider to OpenAI or Ollama

#---------------------------------
# Access the environment variables
#---------------------------------
HOST = os.getenv('HOST')
API_KEY = os.getenv('API_KEY')

MODEL = os.getenv('MODEL', 'qwen2.5-coder:7b') #'llama3.1:latest')

MAX_TOKENS = 50
TEMPERATURE = 0.5
CTX = 4096

MAX_HISTORY = 4

#---------------------------------
# System prompts
#---------------------------------
SYSTEM_PROMPTS = [
    "You are assigned a role of linux command line assistant.",
    "You are to assist users with their queries.",
    "Ensure you provide accurate and helpful responses to users.",
    "Provide commands only when necessary. Otherwise, reply naturally to user.",
]

#---------------------------------
# User prompts
#---------------------------------
COMMAND_PROMPTS = [
    "Generate a sequence of Linux commands to accomplish the task: {task_description}.",
    "Expected output:",
    "- Only list valid Linux commands for the task, each on a new line.",
    "- If command can't be split into multiple lines, it's okay to use ; to separate commands.",
    "- No explanations, introductory text, or additional comments are needed.",
    "- Avoid using backticks (``) to wrap commands.",
    "- Maintain clean formatting with no extra characters or spaces.",
    "Example 1: User requests to list files in the current directory",
    "Output:",
    "ls",
    "Example 2: User asks for help with a non-Linux command-related task",
    "Output:",
    "echo 'I am happy to help you with this task.'"
]

CONVERSATION_PROMPTS = [
    "Respond conversationally to the user’s request: {task_description}.",
    "Expected output:",
    "- A friendly, clear response that directly addresses the user's request.",
    "- Avoid using Linux commands or technical jargon unless explicitly requested.",
    "- Keep the tone helpful and approachable.",
    "Example 1: User asks for advice on learning Linux",
    "Output:",
    "Linux is a powerful and flexible operating system! A good way to start learning is by practicing basic commands, reading tutorials, or exploring Linux distributions like Ubuntu or Fedora.",
    "Example 2: User expresses a general inquiry",
    "Output:",
    "I'm here to help! Let me know more about what you need, and I'll do my best to assist."
]


ROUTER_PROMPTS = [
    "Classify the user request into one of the following categories based on {task_description}.",
    "Expected output:",
    "- COMMAND: if the user ask questions about Linux commands, use this label.",
    "- CONVERSATION: if the request requires a conversational response.",
    "Output should be a single category label without explanations or extra text."
]
