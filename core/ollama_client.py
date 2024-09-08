# core/ollama_client.py
import ollama
from core.ui_helpers import UIHelpers

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
        """
        spinner = self.ui_helpers.start_spinner('Generating command with LLM')

        # Add the user's prompt to the history
        self.add_to_history("user", prompt)

        try:
            response = ollama.chat(
                model='llama3.1:latest', 
                messages=self.history,  # Pass history to the chat method
                options={'max_tokens': 50, 'temperature': 0.5}
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="Command generated")
            
            # Store the assistant's response to the history
            self.add_to_history("assistant", response['message']['content'])

            return response['message']['content']
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"
