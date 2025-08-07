import config

class AIClient:
    def __init__(self):
        self.history = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    def add_to_history(self, message):
        """
        Adds a complete message to the history.
        It handles strings, dictionaries, and Pydantic models to ensure
        the history is always a list of valid message dictionaries.
        """
        if isinstance(message, dict):
            # It's already a dictionary (like from Ollama's client)
            self.history.append(message)
        elif hasattr(message, 'model_dump'):
            # It's a Pydantic model (like from OpenAI's client), convert to dict
            self.history.append(message.model_dump(exclude_none=True, warnings=False))
        else:
            # This should not be reached with the current code, but as a fallback
            raise TypeError(f"Unsupported message type for history: {type(message)}")

    def purge_chat_history(self):
        self.history = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    def get_tool_response(self, prompt, tools):
        raise NotImplementedError

    def get_streaming_response(self, prompt):
        raise NotImplementedError