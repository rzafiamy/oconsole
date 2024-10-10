# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


HISTORY_FILE = 'command_history.txt'
PROVIDER = 'openai'  # Set the provider to OpenAI or Ollama

#---------------------------------
# Access the environment variables
#---------------------------------
HOST = os.getenv('HOST')
API_KEY = os.getenv('API_KEY')

MODEL = 'llama3.1:latest'
MAX_TOKENS = 50
TEMPERATURE = 0.5
CTX = 2048
