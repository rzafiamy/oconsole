# Directory tree for 'app/'
```
app/
├── config.py
├── core
│   ├── ai_client.py
│   ├── command_executor.py
│   ├── ollama_client.py
│   ├── openai_client.py
│   ├── storage.py
│   └── ui_helpers.py
├── .env.example
├── .gitignore
├── manager.py
├── oconsole.sh.example
└── requirements.txt

2 directories, 12 files
```

// < app/config.py >
# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


HISTORY_FILE = 'command_history.txt'
PROVIDER = os.getenv('PROVIDER')  # Set the provider to OpenAI or Ollama

#---------------------------------
# Access the environment variables
#---------------------------------
HOST = os.getenv('HOST')
API_KEY = os.getenv('API_KEY')

MODEL = os.getenv('MODEL', 'qwen2.5-coder:7b') #'llama3.1:latest')

MAX_TOKENS = 50
TEMPERATURE = 0.5
CTX = 4096

MAX_HISTORY = 4

#---------------------------------
# System prompts
#---------------------------------
SYSTEM_PROMPTS = [
    "You are assigned a role of linux command line assistant.",
    "You are to assist users with their queries.",
    "Ensure you provide accurate and helpful responses to users.",
    "Provide commands only when necessary. Otherwise, reply naturally to user.",
]

#---------------------------------
# User prompts
#---------------------------------
COMMAND_PROMPTS = [
    "Generate a sequence of Linux commands to accomplish the task: {task_description}.",
    "Expected output:",
    "- Only list valid Linux commands for the task, each on a new line.",
    "- If command can't be split into multiple lines, it's okay to use ; to separate commands.",
    "- No explanations, introductory text, or additional comments are needed.",
    "- Avoid using backticks (``) to wrap commands.",
    "- Maintain clean formatting with no extra characters or spaces.",
    "Example 1: User requests to list files in the current directory",
    "Output:",
    "ls",
    "Example 2: User asks for help with a non-Linux command-related task",
    "Output:",
    "echo 'I am happy to help you with this task.'"
]

CONVERSATION_PROMPTS = [
    "Respond conversationally to the user’s request: {task_description}.",
    "Expected output:",
    "- A friendly, clear response that directly addresses the user's request.",
    "- Avoid using Linux commands or technical jargon unless explicitly requested.",
    "- Keep the tone helpful and approachable.",
    "Example 1: User asks for advice on learning Linux",
    "Output:",
    "Linux is a powerful and flexible operating system! A good way to start learning is by practicing basic commands, reading tutorials, or exploring Linux distributions like Ubuntu or Fedora.",
    "Example 2: User expresses a general inquiry",
    "Output:",
    "I'm here to help! Let me know more about what you need, and I'll do my best to assist."
]


ROUTER_PROMPTS = [
    "Classify the user request into one of the following categories based on {task_description}.",
    "Expected output:",
    "- COMMAND: if the user ask questions about Linux commands, use this label.",
    "- CONVERSATION: if the request requires a conversational response.",
    "Output should be a single category label without explanations or extra text."
]


// < app/core/ai_client.py >
# core/ai_client.py
import config

class AIClient:
    def __init__(self, ui_helpers):
        self.ui_helpers = ui_helpers
        self.history = [
            {"role": "system", "content": ("\n".join(config.SYSTEM_PROMPTS))}
        ]

    def add_to_history(self, role, content):
        """
        Adds a message to the conversation history.
        """
        # Keep onf config.MAX_HISTORY last messages in history
        self.history.append({"role": role, "content": content})
        self.history = self.history[-config.MAX_HISTORY:]

    def purge_chat_history(self):
        """
        Purges the chat history.
        """
        self.history = []

    def get_chat_response(self, prompt):
        """
        Abstract method to be implemented by subclasses to get chat responses.
        """
        raise NotImplementedError("Subclasses should implement this method")

    def get_streaming_response(self, prompt, stream_callback):
        """
        Abstract method to be implemented by subclasses to handle streaming responses.
        """
        raise NotImplementedError("Subclasses should implement this method")


// < app/core/command_executor.py >
import subprocess
import pexpect
import time
from colorama import Fore, Style
from tabulate import tabulate

class CommandExecutor:
    def __init__(self):
        pass

    def run_command(self, command, use_pexpect=False, expected_inputs=None):
        """
        Runs a shell command and returns a structured result.
        Handles interactive commands with `pexpect` when `use_pexpect` is True.
        :param command: The shell command to execute.
        :param use_pexpect: Set to True if the command requires interaction.
        :param expected_inputs: A list of dictionaries with 'prompt' and 'response' to handle expected input.
        :return: A dictionary with 'success' (bool), 'output' or 'error' (str), and 'elapsed_time' (float).
        """
        #print(f"{Fore.CYAN}{Style.BRIGHT}Executing command: {Fore.YELLOW}{command}{Style.RESET_ALL}")
        
        start_time = time.time()  # Track execution time
        
        if use_pexpect and expected_inputs:
            return self._run_interactive_command(command, expected_inputs, start_time)
        else:
            return self._run_non_interactive_command(command, start_time)

    def _run_non_interactive_command(self, command, start_time):
        """
        Runs a non-interactive shell command using subprocess.
        Returns a structured result.
        """
        try:
            # Start the subprocess
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            output, error = process.communicate()

            # Calculate execution time
            elapsed_time = time.time() - start_time

            if process.returncode != 0:
                # Handle the error case
                return {'success': False, 'error': error.strip(), 'elapsed_time': elapsed_time}
            else:
                # Success case: beautify and return output
                return {'success': True, 'output': output.strip(), 'elapsed_time': elapsed_time}
        except Exception as e:
            # Catch any unexpected errors
            return {'success': False, 'error': str(e), 'elapsed_time': time.time() - start_time}

    def _run_interactive_command(self, command, expected_inputs, start_time):
        """
        Runs an interactive shell command using pexpect and handles expected inputs.
        Returns a structured result.
        """
        try:
            # Start the pexpect process
            process = pexpect.spawn(command, encoding='utf-8')

            for input_data in expected_inputs:
                process.expect(input_data['prompt'])  # Wait for the expected prompt
                process.sendline(input_data['response'])  # Send the response

            # Interact and display real-time output
            process.logfile_read = open('command_output.log', 'w')  # Save command output to a log file
            process.interact()

            # Ensure the process completes and capture any remaining output
            process.wait()
            
            elapsed_time = time.time() - start_time
            return {'success': True, 'output': 'Interactive command completed successfully', 'elapsed_time': elapsed_time}

        except pexpect.exceptions.EOF:
            return {'success': False, 'error': 'Command ended unexpectedly (EOF)', 'elapsed_time': time.time() - start_time}
        
        except pexpect.exceptions.TIMEOUT:
            return {'success': False, 'error': 'Command timed out', 'elapsed_time': time.time() - start_time}
        
        except Exception as e:
            return {'success': False, 'error': str(e), 'elapsed_time': time.time() - start_time}

    def _print_successful_output(self, output, elapsed_time):
        """
        Beautify and print the output of a successfully executed command.
        """
        print(f"{Fore.GREEN}{Style.BRIGHT}Command executed successfully!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Execution time: {elapsed_time:.2f} seconds{Style.RESET_ALL}\n")

        # Check if output contains tabular data
        lines = output.splitlines()
        if len(lines) > 1 and all(len(line.split()) > 1 for line in lines):
            rows = [line.split() for line in lines if line]
            headers = rows[0]
            data_rows = rows[1:]
            # Format as a table
            print(tabulate(data_rows, headers=headers, tablefmt="fancy_grid"))
        else:
            # Print plain output
            print(f"{Fore.LIGHTGREEN_EX}{output}{Style.RESET_ALL}")

// < app/core/ollama_client.py >
# core/ollama_client.py
import ollama
from ollama import Client
from core.ui_helpers import UIHelpers
from core.ai_client import AIClient
import config

class OllamaClient(AIClient):
    """
    Class to interact with Ollama API
    """
    def __init__(self):
        super().__init__(UIHelpers())
        headers = {}
        if config.API_KEY:
            headers = {'Authorization': f'Bearer {config.API_KEY}'}
        self.client = Client(host=config.HOST, headers=headers)

    def get_chat_response(self, prompt):
        """
        Get a response from the Ollama Chat API
        """
        spinner = self.ui_helpers.start_spinner('Generating response with LLM')
        self.add_to_history("user", prompt)

        try:
            response = self.client.chat(
                model=config.MODEL,
                messages=self.history,
                options={'max_tokens': config.MAX_TOKENS, 'temperature': config.TEMPERATURE, 'num_ctx': config.CTX}
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="OK")
            self.add_to_history("assistant", response['message']['content'])
            return response['message']['content']
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_streaming_response(self, prompt, stream_callback):
        """
        Get a response from the Ollama Chat API using streaming
        """
        self.ui_helpers.stop_spinner(None, success=True, message="...")
        self.add_to_history("user", prompt)

        try:
            response = self.client.chat(
                model=config.MODEL,
                messages=self.history,
                stream=True,
                options={'max_tokens': config.MAX_TOKENS, 'temperature': config.TEMPERATURE, 'num_ctx': config.CTX}
            )
            for chunk in response:
                stream_callback(chunk['message']['content'])
                self.add_to_history("assistant", chunk['message']['content'])
        except Exception as e:
            return f"Error generating response: {str(e)}"


// < app/core/openai_client.py >
# core/openai_client.py
import openai
from core.ui_helpers import UIHelpers
from core.ai_client import AIClient
import config

class OpenAIClient(AIClient):
    """
    Class to interact with OpenAI API
    """
    def __init__(self):
        super().__init__(UIHelpers())
        if config.API_KEY:
            openai.api_key = config.API_KEY
        if config.HOST:
            openai.base_url = config.HOST

    def set_api_base_url(self, new_url):
        """
        Set the base URL for the OpenAI API
        """
        openai.base_url = new_url

    def get_chat_response(self, prompt):
        """
        Get a response from the OpenAI Chat API
        """
        spinner = self.ui_helpers.start_spinner('Generating response with LLM')
        self.add_to_history("user", prompt)

        try:
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            self.ui_helpers.stop_spinner(spinner, success=True, message="OK")
            self.add_to_history("assistant", response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            self.ui_helpers.stop_spinner(spinner, success=False, message=f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_streaming_response(self, prompt, stream_callback):
        """
        Get a response from the OpenAI Chat API using streaming
        """
        self.ui_helpers.stop_spinner(None, success=True, message="...")
        self.add_to_history("user", prompt)

        try:
            response = openai.chat.completions.create(
                model=config.MODEL,
                messages=self.history,
                stream=True,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            for chunk in response:
                if chunk.choices:
                    message_content = chunk.choices[0].delta.content
                    if message_content:
                        stream_callback(message_content)
                        self.add_to_history("assistant", message_content)
        except Exception as e:
            return f"Error generating response: {str(e)}"


// < app/core/storage.py >
# core/storage.py
import os

class Storage:
    def __init__(self, history_file="command_history.txt"):
        """
        Initialize the Storage class, setting the history file.
        """
        self.history_file = history_file
        # Ensure the file exists
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as file:
                pass

    def store_command(self, command):
        """
        Append a command to the history file.
        """
        try:
            with open(self.history_file, 'a') as file:
                file.write(command + '\n')
        except Exception as e:
            print(f"Error storing command: {str(e)}")

    def load_history(self):
        """
        Load the history of commands from the file and return them as a list.
        """
        try:
            with open(self.history_file, 'r') as file:
                return [line.strip() for line in file.readlines()]
        except Exception as e:
            print(f"Error loading history: {str(e)}")
            return []

    def clear_history(self):
        """
        Clear the history file.
        """
        try:
            with open(self.history_file, 'w') as file:
                pass
            print("History cleared.")
        except Exception as e:
            print(f"Error clearing history: {str(e)}")


// < app/core/ui_helpers.py >
# core/ui_helpers.py
from halo import Halo
from colorama import Fore, Style
from tqdm import tqdm
import time

class UIHelpers:
    def __init__(self):
        self.spinner = None

    def start_spinner(self, text):
        self.spinner = Halo(text=text, spinner='dots')
        self.spinner.start()
        return self.spinner

    def stop_spinner(self, spinner, success=True, message=""):
        if self.spinner:
            if success:
                self.spinner.succeed(message)
            else:
                self.spinner.fail(message)

    def display_progress_bar(self, duration=2, steps=10):
        with tqdm(total=100, desc="Running command", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
            for _ in range(steps):
                pbar.update(100 // steps)
                time.sleep(duration / steps)

    def confirm_execution(self, command):
        print(f"{Fore.CYAN}Generated command: {Style.BRIGHT}{command}")
        return input(f"{Fore.YELLOW}Do you want to run this command? (y/n): ").lower() == 'y'

    def show_final_output(self, output):
        print(f"{Fore.BLUE}Final command output:\n{output}")


// < app/.env.example >
PROVIDER=openai or ollama
HOST=http://localhost:11434
API_KEY=your_api_key

MODEL=""

// < app/.gitignore >
__pycache__/
*.pyc
.env
command_history.txt


// < app/manager.py >
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
        self.first = True
        self.command_executor = CommandExecutor()
        self.ui_helpers = UIHelpers()
        self.storage = Storage(config.HISTORY_FILE)
        self.last_command_output = None
        self.command_history = []
        self.command_plan = []  # Store the commands plan
    
    # ---------------------------------------------------------
    # Plan the task based on user input
    # ---------------------------------------------------------
    def router_task(self, task_description):
        """
        Classify in categories the following user requests.
        """
        print(f"{Fore.BLUE}Classifying user requests: {task_description}")
        
        prompt = ("\n".join(config.ROUTER_PROMPTS)).format(task_description=task_description)
        
        # Get response from LLM, which will be a list of commands
        category = self.client.get_chat_response(prompt).splitlines()
        
        if category:
            # convert 
            print(f"{Fore.YELLOW}Category:{category}")
            if "COMMAND" in category:
                self.plan_task(task_description)
            elif "CONVERSATION" in category:
                self.conversation_task(task_description)
        else:
            print(f"{Fore.RED}No category generated.")
    
    # ---------------------------------------------------------
    # Execute the task based on user input
    # ---------------------------------------------------------
    def plan_task(self, task_description):
        """
        Generates a plan of commands for the given task description. User confirms before execution.
        """
        print(f"{Fore.BLUE}Planning task: {task_description}")
        
        prompt = ("\n".join(config.COMMAND_PROMPTS)).format(task_description=task_description)

        # Get response from LLM, which will be a list of commands
        command_plan = self.client.get_chat_response(prompt).splitlines()

        if command_plan:
            print(f"{Fore.YELLOW}Generated Plan:")

            for i, command in enumerate(command_plan, 1):
                print(f"{i}- {command}")

            self.command_plan = command_plan  # Store the plan for execution
            self.execute_task_plan()
        else:
            print(f"{Fore.RED}No plan generated.")

    # ---------------------------------------------------------
    # Execute Task Plan
    # ---------------------------------------------------------
    def execute_task_plan(self):
        """
        Executes the planned commands one by one or generates a bash script if 'all' is chosen.
        """
        execute_all = False  # Flag to track if the user wants to execute all commands via a bash script
        
        for i, command in enumerate(self.command_plan, 1):
            # print(f"\n{Fore.CYAN}Executing command {i}/{len(self.command_plan)}: {command}")
            
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

    # ----------------------------------------------------------------------
    # Run a single command with progress and error handling.
    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    # Generate a bash script with all the planned commands and executes it after user confirmation.
    # ----------------------------------------------------------------------
    def generate_bash_script(self):
        """
        Generates a bash script with all the planned commands and executes it after user confirmation.
        """
        script_path = "/tmp/task_plan.sh"  # Temporary location for the bash script
        # print(f"{Fore.YELLOW}Generating bash script at {script_path}...")

        with open(script_path, 'w') as script_file:
            script_file.write("#!/bin/bash\n\n")
            for command in self.command_plan:
                script_file.write(f"{command}\n")

        # Make the script executable
        os.chmod(script_path, 0o755)

        # print(f"{Fore.GREEN}Bash script created and made executable.")
        # print(f"{Fore.CYAN}Executing the bash script...")
        
        result = self.command_executor.run_command(f"bash {script_path}")

        if result['success']:
            # print(f"{Fore.GREEN}Script executed successfully!")
            self.last_command_output = result['output']
            self.command_executor._print_successful_output(result['output'], result['elapsed_time'])
        else:
            print(f"{Fore.RED}Script execution failed: {result['error']}")

    # ----------------------------------------------------------------------
    # Command Execution
    # -----------------------------------------------------------------------
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
    
    def conversation_task(self, task_description):
        """
        Initiates a conversation with the user.
        """
        # print(f"{Fore.GREEN}Starting a conversation...")
        conversation_prompt =  ("\n".join(config.COMMAND_PROMPTS)).format(task_description=task_description)
        if self.last_command_output:
            conversation_prompt = f"{self.last_command_output}\n{conversation_prompt}"
            
        def stream_callback(chunk):
            """
            Callback function to handle streaming response chunks.
            """
            print(f"{Fore.CYAN}{chunk}", end='', flush=True)  # Stream the chunks as they arrive

        # Get the streamed response using context and the user's question
        # print(f"{Fore.MAGENTA}Streaming response:")
        self.client.get_streaming_response(conversation_prompt, stream_callback)
    
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
            # print(f"{Fore.MAGENTA}Streaming response:")
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
            if self.first:
                self.first = False
                print(f"\n\n{Fore.LIGHTYELLOW_EX} Describe the task you want to automate:")
                print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'exit' to quit")
                print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'purge to remove messages from the chat history")
                print(f"{Fore.LIGHTYELLOW_EX}\t - Type 'history' to view command history")

            task = input(f"\n\n{Fore.LIGHTYELLOW_EX}>>: ")
             # Add input to readline history
            readline.add_history(task)
            if task.lower() == 'exit':
                print(f"{Fore.GREEN}Exiting...")
                break
            elif task.lower() == 'purge':
                self.client.purge_chat_history()
            elif task.lower() == 'history':
                self.display_history()
            else:
                result = self.run_single_command('clear')
                self.router_task(task)

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()

// < app/oconsole.sh.example >
source venv/bin/activate; python manager.py


// < app/requirements.txt >
ollama
colorama
halo
tqdm
tabulate
pexpect
python-dotenv
openai


