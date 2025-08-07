import ollama
from ollama import Client
from core.ui_helpers import UIHelpers
from core.ai_client import AIClient
import config

class OllamaClient(AIClient):
    """
    Class to interact with Ollama API supporting function calling.
    """
    def __init__(self):
        super().__init__(UIHelpers())
        headers = {}
        if config.API_KEY:
            headers = {'Authorization': f'Bearer {config.API_KEY}'}
        self.client = Client(host=config.HOST, headers=headers)

    def get_chat_response(self, prompt, tools=None, tool_choice="auto"):
        """
        Get a response from the Ollama Chat API, supporting tools.
        """
        spinner = self.ui_helpers.start_spinner('AI is thinking...')
        self.add_to_history("user", prompt)

        try:
            response = self.client.chat(
                model=config.MODEL,
                messages=self.history,
                tools=tools,
                options={'temperature': config.TEMPERATURE}
            )
            message = response['message']
            self.ui_helpers.stop_spinner(spinner, success=True, message="OK")
            self.add_to_history("assistant", message)
            return message

        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error: {str(e)}")
            return {"role": "assistant", "content": f"Error generating response: {str(e)}"}