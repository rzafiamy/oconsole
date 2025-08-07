import requests
import json
import config

class GenericClient:
    def __init__(self):
        self.base_url = config.HOST
        self.api_key = config.API_KEY
        self.model = config.MODEL
        self.history = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def add_user_message(self, content):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, message_dict):
        self.history.append(message_dict)

    def purge_chat_history(self):
        self.history = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    def get_tool_response(self, tools):
        """Gets a standard, non-streaming response from any OpenAI-compatible API."""
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
            "tools": tools,
            "tool_choice": "auto"
        }
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            response_json = response.json()
            return response_json['choices'][0]['message']
        except requests.exceptions.RequestException as e:
            # Return an error message in the expected format
            return {"role": "assistant", "content": f"API Error: {e}"}

    def get_streaming_response(self):
        """Gets a streaming response from any OpenAI-compatible API."""
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True
        }
        full_response = ""
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, stream=True, timeout=60)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line[len('data: '):]
                        if json_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(json_str)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                full_response += content
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue # Ignore empty or malformed lines
        except requests.exceptions.RequestException as e:
            error_message = f"API Error: {e}"
            full_response = error_message
            yield error_message

        self.add_assistant_message({'role': 'assistant', 'content': full_response})