# core/ollama_client.py
import ollama
from ollama import Client
from core.ui_helpers import UIHelpers
import config

class OllamaClient:
    def __init__(self):
        headers = {}
        if config.OLLAMA_API_KEY:
            headers = {'Authorization': f'Bearer {config.OLLAMA_API_KEY}'}
        
        self.client = Client(host=config.OLLAMA_HOST, headers=headers)
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
            response = self.client.chat(
                model=config.OLLAMA_MODEL,
                messages=self.history,  # Pass history to the chat method
                options={'max_tokens': config.OLLAMA_MAX_TOKENS, 'temperature': config.OLLAMA_TEMPERATURE, 'num_ctx':config.OLLAMA_CTX}
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="Response generated")
            
            # Store the assistant's response in the history
            self.add_to_history("assistant", response['message']['content'])

            return response['message']['content']
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_streaming_response(self, prompt, stream_callback):
        """
        Uses Ollama's LLaMA model to generate a streaming response with history.
        Calls a callback function (stream_callback) to handle each chunk of the response.
        """
        # spinner = self.ui_helpers.start_spinner('Generating response with LLM (streaming)')
        # Stop the spinner before starting to stream response
        self.ui_helpers.stop_spinner(None, success=True, message="Processing your question...")

        # Add the user's prompt to the history
        self.add_to_history("user", prompt)

        try:
            # Stream the response from the LLM
            response = self.client.chat(
                model=config.OLLAMA_MODEL,
                messages=self.history,
                stream=True,  # Enable streaming
                options={'max_tokens': config.OLLAMA_MAX_TOKENS, 'temperature': config.OLLAMA_TEMPERATURE, 'num_ctx':config.OLLAMA_CTX}
            )
            for chunk in response:  # Stream chunks of the response
                stream_callback(chunk['message']['content'])  # Call the callback with each chunk
                self.add_to_history("assistant", chunk['message']['content'])  # Append the chunk to history
            # self.ui_helpers.stop_spinner(spinner, success=True, message="Response generated")
        except Exception as e:
            #self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"