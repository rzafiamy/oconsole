import os
from dotenv import load_dotenv

load_dotenv()

HISTORY_FILE = 'command_history.txt'
PROVIDER = os.getenv('PROVIDER', 'ollama')

HOST = os.getenv('HOST')
API_KEY = os.getenv('API_KEY')

MODEL = os.getenv('MODEL', 'llama3.1')

MAX_TOKENS = 1024
TEMPERATURE = 0.5
CTX = 4096
MAX_HISTORY = 10

SYSTEM_PROMPT = """
You are an expert assistant. Your role is to analyze user requests and determine the best tool to accomplish the task.
You have access to the following tools:
- `generate_linux_command`: Use this tool when the user asks for a Linux command or a series of commands to perform a specific action on a file system or operating system.
- `answer_question`: Use this tool for general questions, conversations, or when no other tool is appropriate.

Based on the user's prompt, choose the correct tool. If the user is just having a conversation, use the `answer_question` tool.
"""