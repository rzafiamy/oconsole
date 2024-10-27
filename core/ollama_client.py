# core/ollama_client.py
import ollama
from ollama import Client
from core.ui_helpers import UIHelpers
from core.ai_client import AIClient
import config

class OllamaClient(AIClient):
    """
    Class to interact with Ollama API
    """
    def __init__(self):
        super().__init__(UIHelpers())
        headers = {}
        if config.API_KEY:
            headers = {'Authorization': f'Bearer {config.API_KEY}'}
        self.client = Client(host=config.HOST, headers=headers)

    def get_chat_response(self, prompt):
        """
        Get a response from the Ollama Chat API
        """
        spinner = self.ui_helpers.start_spinner('Generating response with LLM')
        self.add_to_history("user", prompt)

        try:
            response = self.client.chat(
                model=config.MODEL,
                messages=self.history,
                options={'max_tokens': config.MAX_TOKENS, 'temperature': config.TEMPERATURE, 'num_ctx': config.CTX}
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="Response generated")
            self.add_to_history("assistant", response['message']['content'])
            return response['message']['content']
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_streaming_response(self, prompt, stream_callback):
        """
        Get a response from the Ollama Chat API using streaming
        """
        self.ui_helpers.stop_spinner(None, success=True, message="Processing your question...")
        self.add_to_history("user", prompt)

        try:
            response = self.client.chat(
                model=config.MODEL,
                messages=self.history,
                stream=True,
                options={'max_tokens': config.MAX_TOKENS, 'temperature': config.TEMPERATURE, 'num_ctx': config.CTX}
            )
            for chunk in response:
                stream_callback(chunk['message']['content'])
                self.add_to_history("assistant", chunk['message']['content'])
        except Exception as e:
            return f"Error generating response: {str(e)}"
