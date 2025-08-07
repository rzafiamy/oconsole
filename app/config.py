import os
from dotenv import load_dotenv

load_dotenv()

# --- Connection Settings ---
# Set the base URL of the OpenAI-compatible API.
# - For local Ollama: "http://localhost:11434/v1"
# - For Groq: "https://api.groq.com/openai/v1"
HOST = os.getenv('HOST', 'http://localhost:11434/v1')

# Your API key. For local models, this can often be a dummy string like "ollama".
API_KEY = os.getenv('API_KEY')

# The specific model to use with the provider.
MODEL = os.getenv('MODEL', 'llama3.1')


# --- App Settings ---
HISTORY_FILE = '.python_history'
SYSTEM_PROMPT = """
You are oconsole, a helpful and expert AI command-line assistant.
- Your primary goal is to generate accurate Linux commands based on the user's request.
- When asked a general question, provide a helpful, conversational response.
- Analyze the user's request and use the available tools to respond.
"""