from core.ollama_client import OllamaClient
from core.openai_client import OpenAIClient
from colorama import Fore
from core.command_executor import CommandExecutor
from core.ui_helpers import UIHelpers
from core.storage import Storage
import config
import readline
import os

class TaskManager:
    def __init__(self):
        if config.PROVIDER == 'openai':
            self.client = OpenAIClient()
        else:
            self.client = OllamaClient()
        self.command_executor = CommandExecutor()
        self.ui_helpers = UIHelpers()
        self.storage = Storage(config.HISTORY_FILE)
        self.last_command_output = None
        self.command_history = []
        self.command_plan = []  # Store the commands plan
    
    def plan_task(self, task_description):
        """
        Generates a plan of commands for the given task description. User confirms before execution.
        """
        print(f"{Fore.BLUE}Planning task: {task_description}")
        
        prompt = f"""
        Plan the steps to {task_description} using Linux commands.
        Expected output:
        - A list of Linux commands (without explanations or introductory text).
        - Each command should be separated by a newline.
        - Avoid using backticks (``) to wrap commands.
        - Provide only mandatory steps to complete the task.
        """

        # Get response from LLM, which will be a list of commands
        command_plan = self.client.get_chat_response(prompt).splitlines()

        if command_plan:
            print(f"{Fore.YELLOW}Generated Plan:")
            for i, command in enumerate(command_plan, 1):
                print(f"{i}. {command}")
            
            if self.ui_helpers.confirm_execution("Do you want to proceed with this plan?"):
                self.command_plan = command_plan  # Store the plan for execution
                self.execute_task_plan()
            else:
                print(f"{Fore.RED}Plan rejected by user.")
        else:
            print(f"{Fore.RED}No plan generated.")

    def execute_task_plan(self):
        """
        Executes the planned commands one by one or generates a bash script if 'all' is chosen.
        """
        execute_all = False  # Flag to track if the user wants to execute all commands via a bash script
        
        for i, command in enumerate(self.command_plan, 1):
            print(f"\n{Fore.CYAN}Executing command {i}/{len(self.command_plan)}: {command}")
            
            if not execute_all:  # Only prompt the user if they haven't chosen to execute all
                user_choice = input(f"Do you want to run this command? (y/n/a for all/N for no all): ").strip().lower()
                
                if user_choice == 'y':
                    # Proceed with executing the command normally
                    self.run_single_command(command)
                elif user_choice == 'a':
                    # Generate a bash script with all the commands and execute
                    self.generate_bash_script()
                    return  # Exit after generating and executing the script
                elif user_choice == 'n':
                    print(f"{Fore.YELLOW}Command skipped by user.")
                    continue  # Skip the current command
                elif user_choice == 'N':
                    print(f"{Fore.RED}Cancelling all remaining commands.")
                    break 

    def run_single_command(self, command):
        """
        Run a single command with progress and error handling.
        """
        self.ui_helpers.display_progress_bar()
        result = self.command_executor.run_command(command.strip())

        if result['success']:
            self.last_command_output = result['output']
            self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
            self.storage.store_command(command.strip())
            self.command_history.append(command)
        else:
            print(f"{Fore.RED}Command failed: {result['error']}")
            if not self.handle_failed_command(command, result['error']):
                print(f"{Fore.RED}Skipping this command.")

    def generate_bash_script(self):
        """
        Generates a bash script with all the planned commands and executes it after user confirmation.
        """
        script_path = "/tmp/task_plan.sh"  # Temporary location for the bash script
        print(f"{Fore.YELLOW}Generating bash script at {script_path}...")

        with open(script_path, 'w') as script_file:
            script_file.write("#!/bin/bash\n\n")
            for command in self.command_plan:
                script_file.write(f"{command}\n")

        # Make the script executable
        os.chmod(script_path, 0o755)

        print(f"{Fore.GREEN}Bash script created and made executable.")
        user_confirm = input(f"{Fore.CYAN}Do you want to execute the script now? (y/n): ").strip().lower()

        if user_confirm == 'y':
            print(f"{Fore.CYAN}Executing the bash script...")
            result = self.command_executor.run_command(f"bash {script_path}")

            if result['success']:
                print(f"{Fore.GREEN}Script executed successfully!")
                self.last_command_output = result['output']
                self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
            else:
                print(f"{Fore.RED}Script execution failed: {result['error']}")
        else:
            print(f"{Fore.YELLOW}Script execution cancelled by user.")


    
    def handle_failed_command(self, command, error_message):
        """
        Handles a failed command by prompting the user to retry, skip, or modify.
        Returns True if retry is chosen, False otherwise.
        """
        print(f"{Fore.RED}Command failed with error: {error_message}")
        action = input(f"{Fore.YELLOW}Do you want to retry (r), modify (m), or skip (s) this command? ").strip().lower()
        
        if action == 'r':
            return self.retry_command(command)
        elif action == 'm':
            return self.modify_and_retry_command(command)
        else:
            return False
    
    def retry_command(self, command):
        """
        Retries the same command.
        """
        print(f"{Fore.CYAN}Retrying command: {command}")
        result = self.command_executor.run_command(command.strip())
        
        if result['success']:
            self.last_command_output = result['output']
            self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
            self.storage.store_command(command.strip())
            self.command_history.append(f"Retry for: {command}")
            return True
        else:
            print(f"{Fore.RED}Retry failed: {result['error']}")
            return False
    
    def modify_and_retry_command(self, command):
        """
        Modifies the command before retrying it.
        """
        suggestion = input(f"{Fore.CYAN}Enter a modified command: ").strip()
        if suggestion:
            print(f"{Fore.CYAN}Running modified command: {suggestion}")
            result = self.command_executor.run_command(suggestion.strip())
            
            if result['success']:
                self.last_command_output = result['output']
                self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
                self.storage.store_command(suggestion.strip())
                self.command_history.append(f"Modified command for: {command}")
                return True
            else:
                print(f"{Fore.RED}Modified command failed: {result['error']}")
                return False
        else:
            print(f"{Fore.RED}No modified command entered.")
            return False
    
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
            self.client.get_streaming_response(context, stream_callback)


    def display_history(self):
        """
        Display the command history.
        """
        print(f"{Fore.GREEN}Command History:")
        for i, command in enumerate(self.command_history, 1):
            print(f"{i}. {command}")    
    def start(self):
        """
        Starts an interactive command-line loop for task planning and execution.
        """
        print(f"{Fore.MAGENTA}-"*100)
        print(f"{Fore.MAGENTA}Welcome to the Python LLM-powered Task Planner and Executor!")
        print(f"{Fore.MAGENTA}-"*100)
        
        for cmd in self.storage.load_history():
            readline.add_history(cmd)

        while True:
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
                self.client.purge_chat_history()
            elif task.lower() == 'history':
                self.display_history()
            elif task.lower() == 'ask':
                self.ask_about_output()
            else:
                self.plan_task(task)

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()