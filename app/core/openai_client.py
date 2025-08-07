import openai
from core.ui_helpers import UIHelpers
from core.ai_client import AIClient
import config

class OpenAIClient(AIClient):
    """
    Class to interact with OpenAI API supporting function calling.
    """
    def __init__(self):
        super().__init__(UIHelpers())
        if config.API_KEY:
            openai.api_key = config.API_KEY
        if config.HOST:
            openai.base_url = config.HOST

    def get_chat_response(self, prompt, tools=None, tool_choice="auto"):
        """
        Get a response from the OpenAI Chat API, supporting tools.
        """
        spinner = self.ui_helpers.start_spinner('AI is thinking...')
        self.add_to_history("user", prompt)

        try:
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,
                tools=tools,
                tool_choice=tool_choice,
                temperature=config.TEMPERATURE
            )
            message = response.choices[0].message
            self.ui_helpers.stop_spinner(spinner, success=True, message="OK")
            self.add_to_history("assistant", message)
            return message

        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error: {str(e)}")
            return {"role": "assistant", "content": f"Error generating response: {str(e)}"}