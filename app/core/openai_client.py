import openai
from core.ai_client import AIClient
import config

class OpenAIClient(AIClient):
    def __init__(self):
        super().__init__()
        openai.api_key = config.API_KEY
        if config.HOST:
            openai.base_url = config.HOST

    def get_tool_response(self, prompt, tools):
        self.add_to_history({'role': 'user', 'content': prompt})
        response = openai.chat.completions.create(
            model=config.MODEL,
            messages=self.history,
            tools=tools,
            tool_choice="auto"
        )
        message = response.choices[0].message
        self.add_to_history(message)
        return message

    def get_streaming_response(self, prompt):
        self.add_to_history({'role': 'user', 'content': prompt})
        stream = openai.chat.completions.create(
            model=config.MODEL,
            messages=self.history,
            stream=True
        )
        full_response = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            yield content
        self.add_to_history({'role': 'assistant', 'content': full_response})