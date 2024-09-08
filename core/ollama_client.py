# core/ollama_client.py
import ollama
from core.ui_helpers import UIHelpers
import config

class OllamaClient:
    def __init__(self):
        self.ui_helpers = UIHelpers()
        self.history = []

    def add_to_history(self, role, content):
        """
        Adds a message to the conversation history.
        """
        self.history.append({"role": role, "content": content})

    def get_chat_response(self, prompt):
        """
        Uses Ollama's LLaMA model to generate a chat response with history.
        The prompt can include previous command output as context.
        """
        spinner = self.ui_helpers.start_spinner('Generating response with LLM')

        # Add the user's prompt to the history
        self.add_to_history("user", prompt)

        try:
            response = ollama.chat(
                model=config.OLLAMA_MODEL,
                messages=self.history,  # Pass history to the chat method
                options={'max_tokens': config.OLLAMA_MAX_TOKENS, 'temperature': config.OLLAMA_TEMPERATURE}
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="Response generated")
            
            # Store the assistant's response in the history
            self.add_to_history("assistant", response['message']['content'])

            return response['message']['content']
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"