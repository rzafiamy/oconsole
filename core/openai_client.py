import openai
from core.ui_helpers import UIHelpers
import config

class OpenAIClient:
    def __init__(self):
        headers = {}
        if config.API_KEY:
            openai.api_key = config.API_KEY

        # Set the API base URL dynamically if provided in the config
        if config.HOST:
            openai.base_url = config.HOST
        
        self.ui_helpers = UIHelpers()
        self.history = []

    def set_api_base_url(self, new_url):
        """
        Allows changing the OpenAI API base URL at runtime.
        """
        openai.base_url = new_url

    def add_to_history(self, role, content):
        """
        Adds a message to the conversation history.
        """
        self.history.append({"role": role, "content": content})

    def get_chat_response(self, prompt):
        """
        Uses OpenAI's model to generate a chat response with history.
        The prompt can include previous command output as context.
        """
        spinner = self.ui_helpers.start_spinner('Generating response with LLM')

        # Add the user's prompt to the history
        self.add_to_history("user", prompt)

        try:
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,  # Pass history to the chat method
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="Response generated")

            # Store the assistant's response in the history
            self.add_to_history("assistant", response.choices[0].message.content)

            return response.choices[0].message.content
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_streaming_response(self, prompt, stream_callback):
        """
        Uses OpenAI's model to generate a streaming response with history.
        Calls a callback function (stream_callback) to handle each chunk of the response.
        """
        self.ui_helpers.stop_spinner(None, success=True, message="Processing your question...")

        # Add the user's prompt to the history
        self.add_to_history("user", prompt)

        try:
            # Stream the response from the LLM
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,
                stream=True,  # Enable streaming
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            for chunk in response:  # Stream chunks of the response
                if chunk.choices:
                    message_content = chunk.choices[0].delta.content
                    if message_content:
                        stream_callback(message_content)  # Call the callback with each chunk
                        self.add_to_history("assistant", message_content)  # Append the chunk to history
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def purge_chat_history(self):
        """
        Purges the chat history.
        """
        self.history = []
