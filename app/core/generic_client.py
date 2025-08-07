# app/core/generic_client.py
import requests
import json
import config
import time

# This client is now STATELESS. It does not hold its own history.
# The history is managed by the TaskManager and passed in for each call.
class GenericClient:
    def __init__(self):
        self.base_url = config.HOST
        self.api_key = config.API_KEY
        self.model = config.MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def get_tool_response(self, messages, tools):
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages, # Use passed-in messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        last_error = None
        for attempt in range(3):
            try:
                response = requests.post(endpoint, headers=self.headers, json=payload, timeout=60)
                response.raise_for_status()

                try:
                    response_json = response.json()
                except json.JSONDecodeError:
                    return {"role": "assistant", "content": "API Error: Received an invalid response from the server."}
                
                if not response_json or 'choices' not in response_json or not response_json['choices']:
                    return {"role": "assistant", "content": "API Error: Received an empty or malformed response from the server."}

                return response_json['choices'][0]['message']
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(2)
        
        return {"role": "assistant", "content": f"API Connection Error: {last_error}"}

    def get_streaming_response(self, messages):
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages, # Use passed-in messages
            "stream": True
        }
        full_response = ""
        last_error = None
        
        for attempt in range(3):
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
                                continue
                return
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(2)

        error_message = f"API Connection Error: {last_error}"
        yield error_message