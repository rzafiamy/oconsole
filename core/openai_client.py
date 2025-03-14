# core/openai_client.py
import openai
from core.ui_helpers import UIHelpers
from core.ai_client import AIClient
import config

class OpenAIClient(AIClient):
    """
    Class to interact with OpenAI API
    """
    def __init__(self):
        super().__init__(UIHelpers())
        if config.API_KEY:
            openai.api_key = config.API_KEY
        if config.HOST:
            openai.base_url = config.HOST

    def set_api_base_url(self, new_url):
        """
        Set the base URL for the OpenAI API
        """
        openai.base_url = new_url

    def get_chat_response(self, prompt):
        """
        Get a response from the OpenAI Chat API
        """
        spinner = self.ui_helpers.start_spinner('Generating response with LLM')
        self.add_to_history("user", prompt)

        try:
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="OK")
            self.add_to_history("assistant", response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_streaming_response(self, prompt, stream_callback):
        """
        Get a response from the OpenAI Chat API using streaming
        """
        self.ui_helpers.stop_spinner(None, success=True, message="...")
        self.add_to_history("user", prompt)

        try:
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,
                stream=True,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            for chunk in response:
                if chunk.choices:
                    message_content = chunk.choices[0].delta.content
                    if message_content:
                        stream_callback(message_content)
                        self.add_to_history("assistant", message_content)
        except Exception as e:
            return f"Error generating response: {str(e)}"
