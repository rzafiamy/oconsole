# core/ai_client.py
import config

class AIClient:
    def __init__(self, ui_helpers):
        self.ui_helpers = ui_helpers
        self.history = [
            {"role": "system", "content": ("\n".join(config.SYSTEM_PROMPTS))}
        ]

    def add_to_history(self, role, content):
        """
        Adds a message to the conversation history.
        """
        # Keep onf config.MAX_HISTORY last messages in history
        self.history.append({"role": role, "content": content})
        self.history = self.history[-config.MAX_HISTORY:]

    def purge_chat_history(self):
        """
        Purges the chat history.
        """
        self.history = []

    def get_chat_response(self, prompt):
        """
        Abstract method to be implemented by subclasses to get chat responses.
        """
        raise NotImplementedError("Subclasses should implement this method")

    def get_streaming_response(self, prompt, stream_callback):
        """
        Abstract method to be implemented by subclasses to handle streaming responses.
        """
        raise NotImplementedError("Subclasses should implement this method")
