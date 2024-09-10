from core.ollama_client import OllamaClient
from colorama import Fore
from core.command_executor import CommandExecutor
from core.ui_helpers import UIHelpers
from core.storage import Storage
import config
import readline

class TaskManager:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.command_executor = CommandExecutor()
        self.ui_helpers = UIHelpers()
        self.storage = Storage(config.HISTORY_FILE)
        self.last_command_output = None  # Store the last command output here
        self.command_history = []  # Store the history of commands typed

    def automate_task(self, task_description):
        """
        Takes a task description, uses LLM to generate a command, and executes it.
        If the command fails, sends error output back to AI for new suggestions.
        """
        prompt = f"""
        Generate one Linux command to {task_description}.
        Expected output:
        - One linux command that performs the task described without introductory words.
        - Avoid using backticks (``) to wrap commands.
        """

        # Get the response using history-enabled chat method
        command = self.ollama_client.get_chat_response(prompt)

        if command:
            if self.ui_helpers.confirm_execution(command):
                self.ui_helpers.display_progress_bar()
                
                # Run the command and handle potential errors
                result = self.command_executor.run_command(command.strip())

                if result['success']:
                    # If the command was successful, store the output
                    self.last_command_output = result['output']
                    self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
                    self.storage.store_command(command.strip())
                    self.command_history.append(task_description)
                else:
                    # If the command failed, send the error to the AI model
                    self.handle_command_failure(command.strip(), result['error'])
            else:
                print(f"{Fore.RED}Command not run.")
        else:
            print(f"{Fore.RED}No command generated.")


    def handle_command_failure(self, command, error_message):
        """
        Sends error output back to AI for new suggestions and retries the command.
        """
        print(f"{Fore.RED}Command failed with error: {error_message}")
        
        # Send error message back to AI for suggestions
        error_prompt = f"""
        The following command failed: {command}
        Error message: {error_message}
        Please suggest an alternative command to achieve the same task.
         Expected output:
        - One linux alternative command that performs the task described without introductory words.
        - Avoid using backticks (``) to wrap commands.
        """
        suggestion = self.ollama_client.get_chat_response(error_prompt)

        if suggestion:
            print(f"{Fore.YELLOW}AI Suggestion: {suggestion}")
            if self.ui_helpers.confirm_execution(suggestion):
                self.ui_helpers.display_progress_bar()
                result = self.command_executor.run_command(suggestion.strip())
                
                if result['success']:
                    self.last_command_output = result['output']
                    self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
                    self.storage.store_command(suggestion.strip())
                    self.command_history.append(f"Retry for: {command}")
                else:
                    print(f"{Fore.RED}Retry failed. Error: {result['error']}")
            else:
                print(f"{Fore.RED}Suggested command not run.")
        else:
            print(f"{Fore.RED}No alternative command generated.")

    def ask_about_output(self):
        """
        Allows the user to ask questions about the last command output.
        Streams the response for a more interactive experience.
        """
 
        while True:
            print()
            question = input(f"{Fore.CYAN}What do you want to ask about the last command output (/back to return) ?: ")

            if question.strip().lower() == '/back':
                print(f"{Fore.GREEN}Exiting ask mode and returning to the main menu.")
                break

            # Combine the last command output with the user's question
            context = f"""
            Your are an expert on admin sys linux and devops. 
            Reply to user question about the last command output.
            Command output:
            {self.last_command_output}
            Now, {question}
            Expected output:
            - A response to the user's question based on the last command output.
            - Strucutred response with no introductory words.
            - Try to reply in different paragraphs with title and content.
            """

            def stream_callback(chunk):
                """
                Callback function to handle streaming response chunks.
                """
                print(f"{Fore.CYAN}{chunk}", end='', flush=True)  # Stream the chunks as they arrive

            # Get the streamed response using context and the user's question
            print(f"{Fore.MAGENTA}Streaming response:")
            self.ollama_client.get_streaming_response(context, stream_callback)


    def display_history(self):
        """
        Display the command history.
        """
        print(f"{Fore.GREEN}Command History:")
        for i, command in enumerate(self.command_history, 1):
            print(f"{i}. {command}")

    def start(self):
        """
        Starts an interactive command-line loop for automating tasks.
        """
        print(f"{Fore.MAGENTA}-"*100)
        print(f"{Fore.MAGENTA}Welcome to the Python LLM-powered command interpreter!")
        print(f"{Fore.MAGENTA}-"*100)
        
        # Load command history into readline
        for cmd in self.storage.load_history():
            readline.add_history(cmd)

        while True:
            #add new line
            print()
            print(f"{Fore.LIGHTYELLOW_EX} Describe the task you want to automate:")
            print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'exit' to quit")
            print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'purge to remove messages from the chat history")
            print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'history' to view command history")
            print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'ask' to ask questions about the last command output")

            task = input(f"{Fore.LIGHTYELLOW_EX}>>: ")
            
            # Add input to readline history
            readline.add_history(task)
            
            if task.lower() == 'exit':
                print(f"{Fore.GREEN}Exiting...")
                break
            elif task.lower() == 'purge':
                self.ollama_client.purge_chat_history()
            elif task.lower() == 'history':
                self.display_history()
            elif task.lower() == 'ask':
                self.ask_about_output()
            else:
                self.automate_task(task)

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()
