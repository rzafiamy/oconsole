import config

class AIClient:
    def __init__(self, ui_helpers):
        self.ui_helpers = ui_helpers
        self.history = [
            {"role": "system", "content": config.SYSTEM_PROMPT}
        ]

    def add_to_history(self, role, content):
        """
        Adds a message to the conversation history.
        """
        if content is None:
            return
        # If the last message was from the same role, append content
        if self.history and self.history[-1]["role"] == role:
            # Ensure content is a string before concatenating
            if isinstance(self.history[-1]["content"], str):
                 self.history[-1]["content"] += str(content)
            # If it's a list (e.g., tool calls), handle appropriately
            else:
                 self.history.append({"role": role, "content": content})
        else:
            self.history.append({"role": role, "content": content})

        # Trim history to MAX_HISTORY length
        if len(self.history) > config.MAX_HISTORY:
            # Keep the system prompt and the most recent interactions
            self.history = [self.history[0]] + self.history[-config.MAX_HISTORY:]

    def purge_chat_history(self):
        """
        Purges the chat history, keeping only the system prompt.
        """
        self.history = [
            {"role": "system", "content": config.SYSTEM_PROMPT}
        ]
        print("Chat history has been purged.")

    def get_chat_response(self, prompt, tools=None, tool_choice="auto"):
        """
        Abstract method to be implemented by subclasses to get chat responses,
        with optional support for tools.
        """
        raise NotImplementedError("Subclasses should implement this method")