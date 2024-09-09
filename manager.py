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
                result = self.command_executor.run_command(command.strip())

                # Store the output of the command for context in later questions
                self.last_command_output = result
                self.storage.store_command(command.strip())
                self.command_history.append(task_description)  # Add to history

                # self.ui_helpers.show_final_output(result)
            else:
                print(f"{Fore.RED}Command not run.")
        else:
            print(f"{Fore.RED}No command generated.")

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
            context = f"Here is the command output:\n{self.last_command_output}\n\nNow, {question}"


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
            print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'history' to view command history")
            print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'ask' to ask questions about the last command output")

            task = input(f"{Fore.LIGHTYELLOW_EX}>>: ")
            
            # Add input to readline history
            readline.add_history(task)
            
            if task.lower() == 'exit':
                print(f"{Fore.GREEN}Exiting...")
                break
            elif task.lower() == 'history':
                self.display_history()
            elif task.lower() == 'ask':
                self.ask_about_output()
            else:
                self.automate_task(task)

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()
