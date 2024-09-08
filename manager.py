# manager.py
from core.ollama_client import OllamaClient
from core.command_executor import CommandExecutor
from colorama import Fore, Style
from core.ui_helpers import UIHelpers
from core.storage import Storage
import config

class TaskManager:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.command_executor = CommandExecutor()
        self.ui_helpers = UIHelpers()
        self.storage = Storage(config.HISTORY_FILE)

    def automate_task(self, task_description):
        """
        Takes a task description, uses LLM to generate a command, and executes it.
        """
        prompt = f"Generate one Linux command to {task_description}.\nExpected output: One linux command that performs the task described without introductory words."

        # Get the response using history-enabled chat method
        command = self.ollama_client.get_chat_response(prompt)

        if command:
            if self.ui_helpers.confirm_execution(command):
                self.ui_helpers.display_progress_bar()
                result = self.command_executor.run_command(command.strip())
                
                # Store the executed command in the history file
                self.storage.store_command(command.strip())
                
                self.ui_helpers.show_final_output(result)
            else:
                print(f"{Fore.RED}Command not run.")
        else:
            print(f"{Fore.RED}No command generated.")

    def display_history(self):
        """
        Loads and displays the command history from the file.
        """
        history = self.storage.load_history()
        if history:
            print(f"{Fore.MAGENTA}Command History:")
            for index, command in enumerate(history, 1):
                print(f"{Fore.CYAN}{index}. {command}")
        else:
            print(f"{Fore.RED}No history available.")

    def start(self):
        """
        Starts an interactive command-line loop for automating tasks.
        """
        print(f"{Fore.MAGENTA}Welcome to the Python LLM-powered command interpreter!")
        while True:
            task = input(f"{Fore.LIGHTYELLOW_EX}Describe the task (or type 'exit' to quit, 'history' to view command history): ")
            if task.lower() == 'exit':
                print(f"{Fore.GREEN}Exiting...")
                break
            elif task.lower() == 'history':
                self.display_history()
            else:
                self.automate_task(task)

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()
