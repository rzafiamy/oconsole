# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
OLLAMA_HOST = os.getenv('HOST')
OLLAMA_API_KEY = os.getenv('API_KEY')

print(OLLAMA_HOST)
print(OLLAMA_API_KEY)

OLLAMA_MODEL = 'llama3.1:latest'
OLLAMA_MAX_TOKENS = 50
OLLAMA_TEMPERATURE = 0.5
HISTORY_FILE = 'command_history.txt'
