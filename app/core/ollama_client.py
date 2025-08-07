from ollama import Client
from core.ai_client import AIClient
import config

class OllamaClient(AIClient):
    def __init__(self):
        super().__init__()
        self.client = Client(host=config.HOST)

    def get_tool_response(self, prompt, tools):
        self.add_to_history({'role': 'user', 'content': prompt})
        response = self.client.chat(
            model=config.MODEL,
            messages=self.history,
            tools=tools
        )
        message = response['message']
        self.add_to_history(message)
        return message

    def get_streaming_response(self, prompt):
        self.add_to_history({'role': 'user', 'content': prompt})
        stream = self.client.chat(
            model=config.MODEL,
            messages=self.history,
            stream=True
        )
        full_response = ""
        for chunk in stream:
            content = chunk['message']['content']
            full_response += content
            yield content
        self.add_to_history({'role': 'assistant', 'content': full_response})