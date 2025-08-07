import requests
import json
import config

class GenericClient:
    def __init__(self):
        self.base_url = config.HOST
        self.api_key = config.API_KEY
        self.model = config.MODEL
        # --- THIS IS THE FIX ---
        # History is now initialized empty. The system prompt is set by the TaskManager.
        self.history = []
        # --- END OF FIX ---
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def add_user_message(self, content):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, message_dict):
        self.history.append(message_dict)

    def add_tool_response_message(self, tool_call_id, content):
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def purge_chat_history(self):
        # This method is now effectively handled by creating a new client instance
        # but we can leave it for clarity.
        self.history = []

    def get_tool_response(self, tools):
        """
        Gets a standard, non-streaming response. This function ONLY uses 'return'.
        """
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

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
            return {"role": "assistant", "content": f"API Connection Error: {e}"}

    def get_streaming_response(self):
        """
        Gets a streaming response. This function ONLY uses 'yield'.
        """
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
                            continue
        except requests.exceptions.RequestException as e:
            error_message = f"API Connection Error: {e}"
            full_response = error_message
            yield error_message
        
        self.add_assistant_message({'role': 'assistant', 'content': full_response})