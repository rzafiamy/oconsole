from core.ollama_client import OllamaClient
from core.openai_client import OpenAIClient
from colorama import Fore, Style
from core.command_executor import CommandExecutor
from core.ui_helpers import UIHelpers
from core.storage import Storage
from core import tools
import config
import readline
import os
import json

class TaskManager:
    def __init__(self):
        if config.PROVIDER == 'openai':
            self.client = OpenAIClient()
        else:
            self.client = OllamaClient()

        self.command_executor = CommandExecutor()
        self.ui_helpers = UIHelpers()
        self.storage = Storage(config.HISTORY_FILE)
        self.command_plan = []

    def process_task(self, task_description):
        """
        Processes a user task by calling the LLM with available tools,
        executing the chosen tool, and formatting the response as JSON.
        """
        print(f"{Fore.BLUE}Processing request...{Style.RESET_ALL}")

        # 1. Get the LLM's decision on which tool to use
        tool_definitions = tools.get_tools()
        response_message = self.client.get_chat_response(task_description, tools=tool_definitions)

        # 2. Check if the LLM decided to use a tool
        tool_calls = getattr(response_message, 'tool_calls', None)
        if not tool_calls:
            # Handle direct conversational response
            content = getattr(response_message, 'content', str(response_message))
            formatted_json = tools.format_response(
                data={"response": content},
                schema=tools.CONVERSATION_RESPONSE_SCHEMA
            )
            print(f"\n{Fore.GREEN}AI Response:{Style.RESET_ALL}")
            print(formatted_json)
            return

        # 3. Execute the chosen tool
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                print(f"{Fore.RED}Error decoding arguments for tool {function_name}.{Style.RESET_ALL}")
                continue

            print(f"{Fore.YELLOW}AI decided to use tool: {Style.BRIGHT}{function_name}{Style.RESET_ALL}")

            if function_name == "generate_linux_command":
                # The LLM generates the commands directly
                task = arguments.get('task_description', '')
                prompt = f"Generate only the linux command(s) for the following task, each on a new line, with no explanation: {task}"
                
                # We call the LLM again, but without tools, to get the raw command
                command_response = self.client.get_chat_response(prompt, tools=None)
                command_list = command_response.content.strip().splitlines()

                self.command_plan = [cmd for cmd in command_list if cmd] # Filter out empty lines
                if not self.command_plan:
                    print(f"{Fore.RED}The AI did not generate any commands.{Style.RESET_ALL}")
                    continue

                # Format the response into the specified JSON format
                formatted_json = tools.format_response(
                    data={"commands": self.command_plan},
                    schema=tools.COMMAND_RESPONSE_SCHEMA
                )
                print(f"\n{Fore.GREEN}Generated Plan:{Style.RESET_ALL}")
                print(formatted_json)

                # Execute the generated command plan
                self.execute_task_plan()

            elif function_name == "answer_question":
                query = arguments.get('query', '')
                formatted_json = tools.format_response(
                    data={"response": query},
                    schema=tools.CONVERSATION_RESPONSE_SCHEMA
                )
                print(f"\n{Fore.GREEN}AI Response:{Style.RESET_ALL}")
                print(formatted_json)

    def execute_task_plan(self):
        """
        Executes the planned commands, asking for user confirmation.
        (This function is adapted from your original code)
        """
        if not self.command_plan:
            print(f"{Fore.YELLOW}No command plan to execute.{Style.RESET_ALL}")
            return

        user_choice = input(f"\n{Fore.YELLOW}Do you want to run the generated command(s)? (y/n/a for all): {Style.RESET_ALL}").strip().lower()

        if user_choice == 'y':
            for command in self.command_plan:
                self.run_single_command(command)
        elif user_choice == 'a':
            self.generate_and_run_bash_script()
        else:
            print(f"{Fore.RED}Execution cancelled by user.{Style.RESET_ALL}")

    def run_single_command(self, command):
        """
        Runs a single command and prints the result.
        (This function is adapted from your original code)
        """
        print(f"\n{Fore.CYAN}Executing: {Style.BRIGHT}{command}{Style.RESET_ALL}")
        self.ui_helpers.display_progress_bar()
        result = self.command_executor.run_command(command.strip())

        if result['success']:
            self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
            self.storage.store_command(command.strip())
        else:
            print(f"{Fore.RED}Command failed: {result['error']}{Style.RESET_ALL}")

    def generate_and_run_bash_script(self):
        """
        Generates and executes a bash script with all planned commands.
        (This function is adapted from your original code)
        """
        script_path = "/tmp/oconsole_plan.sh"
        print(f"{Fore.YELLOW}Generating and executing bash script at {script_path}...{Style.RESET_ALL}")

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\nset -e\n\n")
            for command in self.command_plan:
                f.write(f"{command}\n")

        os.chmod(script_path, 0o755)
        self.run_single_command(f"bash {script_path}")

    def start(self):
        """
        Starts the interactive command-line loop.
        """
        print(f"{Fore.MAGENTA}{'-'*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Welcome to your AI-Powered Command Line Assistant{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'-'*60}{Style.RESET_ALL}")
        print(f"Using provider: {Fore.YELLOW}{config.PROVIDER}{Style.RESET_ALL} with model: {Fore.YELLOW}{config.MODEL}{Style.RESET_ALL}")
        
        for cmd in self.storage.load_history():
            readline.add_history(cmd)

        while True:
            print(f"\n{Fore.BLUE}Type your request, or 'exit' to quit, 'purge' to clear history.{Style.RESET_ALL}")
            try:
                task = input(f"{Fore.LIGHTYELLOW_EX}>> {Style.RESET_ALL}")
                readline.add_history(task)

                if task.lower() == 'exit':
                    print(f"{Fore.GREEN}Exiting...{Style.RESET_ALL}")
                    break
                elif task.lower() == 'purge':
                    self.client.purge_chat_history()
                elif task.strip():
                    self.process_task(task)

            except (KeyboardInterrupt, EOFError):
                print(f"\n{Fore.GREEN}Exiting...{Style.RESET_ALL}")
                break

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()