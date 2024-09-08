# manager.py
from core.ollama_client import OllamaClient
from colorama import Fore, Style
from core.command_executor import CommandExecutor
from core.ui_helpers import UIHelpers
from core.storage import Storage
import config

class TaskManager:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.command_executor = CommandExecutor()
        self.ui_helpers = UIHelpers()
        self.storage = Storage(config.HISTORY_FILE)
        self.last_command_output = None  # Store the last command output here

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

                # Store the output of the command for context in later questions
                self.last_command_output = result
                self.storage.store_command(command.strip())

                self.ui_helpers.show_final_output(result)
            else:
                print(f"{Fore.RED}Command not run.")
        else:
            print(f"{Fore.RED}No command generated.")

    def ask_about_output(self, question):
        """
        Allows the user to ask questions about the last command output.
        """
        if not self.last_command_output:
            print(f"{Fore.RED}No command output available to ask questions about.")
            return

        # Combine the last command output with the user's question
        context = f"Here is the command output:\n{self.last_command_output}\n\nNow, {question}"
        
        # Pass the context along with the question to the LLM
        response = self.ollama_client.get_chat_response(context)
        print(f"{Fore.CYAN}Answer:\n{response}")

    def start(self):
        """
        Starts an interactive command-line loop for automating tasks.
        """
        print(f"{Fore.MAGENTA}Welcome to the Python LLM-powered command interpreter!")
        while True:
            task = input(f"{Fore.LIGHTYELLOW_EX}Describe the task (or type 'exit' to quit, 'history' to view command history, 'ask' to ask questions about the last command output): ")
            if task.lower() == 'exit':
                print(f"{Fore.GREEN}Exiting...")
                break
            elif task.lower() == 'history':
                self.display_history()
            elif task.lower() == 'ask':
                question = input(f"{Fore.LIGHTYELLOW_EX}What do you want to ask about the last command output?: ")
                self.ask_about_output(question)
            else:
                self.automate_task(task)

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()
