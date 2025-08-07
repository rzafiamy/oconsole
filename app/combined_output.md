# Directory tree for 'app/'
```
app/
├── command_history.txt
├── config.py
├── core
│   ├── ai_client.py
│   ├── command_executor.py
│   ├── generic_client.py
│   ├── memory.py
│   ├── storage.py
│   ├── tools.py
│   └── ui_helpers.py
├── .env.example
├── .gitignore
├── launcher.sh
├── manager.py
├── oconsole.sh.example
├── .python_history
└── requirements.txt

2 directories, 16 files
```

// < app/config.py >
import os
from dotenv import load_dotenv

load_dotenv()

# --- Connection Settings ---
HOST = os.getenv('HOST', 'http://localhost:11434/v1')
API_KEY = os.getenv('API_KEY')
MODEL = os.getenv('MODEL', 'llama3.1')

# --- Agent Settings ---
AGENT_MAX_STEPS = 7 
SAFE_COMMANDS = [
    "ls", "cat", "echo", "pwd", "df", "du", "wc", "grep", 
    "find", "whoami", "uname", "date", "uptime", "journalctl",
    "ps", "netstat", "apt", "dpkg"
]

# --- App Settings ---
HISTORY_FILE = '.python_history'

PLANNER_SYSTEM_PROMPT = """
You are a meticulous planner AI. Your job is to analyze a user's goal and break it down into a concise, numbered list of steps.
You must also determine if the plan is "complex". A plan is considered complex if it requires more than 2 steps.
Respond ONLY with a JSON object in the following format:
{"is_complex": boolean, "plan": ["Step 1...", "Step 2..."]}
"""

# --- THIS IS THE FIX ---
# The new prompt provides much clearer instructions and examples for using arguments.
AGENT_SYSTEM_PROMPT = f"""
You are oconsole, an autonomous AI agent. Your purpose is to execute a pre-approved plan to achieve a user's goal by using the tools available to you.

Your primary tool is `run_safe_command`. You MUST be intelligent when using it. Analyze the user's request and context to determine the correct arguments.

**CRITICAL INSTRUCTIONS:**
1.  **Always use arguments when needed.** Do not just call commands like `ls` or `grep` by themselves. Construct a full `args_string` based on the user's goal.
2.  **Refer to your memory** to use file paths or other information from previous steps as arguments in subsequent steps.

**Examples of Correct Tool Use:**
- **User Goal:** "show me details of my documents folder" -> **AI Action:** `run_safe_command(command_name="ls", args_string="-la ~/Documents")`
- **User Goal:** "how many lines are in my .bashrc file?" -> **AI Action:** `run_safe_command(command_name="wc", args_string="-l ~/.bashrc")`
- **User Goal:** "search for the word 'error' in my system log" -> **AI Action:** `run_safe_command(command_name="grep", args_string="'error' /var/log/syslog")`
- **User Goal:** "find all python files in my projects folder" -> **AI Action:** `run_safe_command(command_name="find", args_string="~/projects -name '*.py'")`

For any task that cannot be accomplished with the safe commands ({", ".join(SAFE_COMMANDS)}), use `generate_linux_command`. When the plan is complete, use `answer_question` to give a final summary.
"""

// < app/core/ai_client.py >
import config

class AIClient:
    def __init__(self):
        self.history = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    def add_to_history(self, message):
        """
        Adds a complete message to the history.
        It handles strings, dictionaries, and Pydantic models to ensure
        the history is always a list of valid message dictionaries.
        """
        if isinstance(message, dict):
            # It's already a dictionary (like from Ollama's client)
            self.history.append(message)
        elif hasattr(message, 'model_dump'):
            # It's a Pydantic model (like from OpenAI's client), convert to dict
            self.history.append(message.model_dump(exclude_none=True, warnings=False))
        else:
            # This should not be reached with the current code, but as a fallback
            raise TypeError(f"Unsupported message type for history: {type(message)}")

    def purge_chat_history(self):
        self.history = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    def get_tool_response(self, prompt, tools):
        raise NotImplementedError

    def get_streaming_response(self, prompt):
        raise NotImplementedError

// < app/core/command_executor.py >
import subprocess
import time
from rich.console import Console
from rich.table import Table

class CommandExecutor:
    def __init__(self):
        self.console = Console()

    def run_command(self, command):
        start_time = time.time()
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                encoding='utf-8'
            )
            output, error = process.communicate()
            elapsed_time = time.time() - start_time

            if process.returncode != 0:
                return {'success': False, 'error': error.strip(), 'elapsed_time': elapsed_time}
            else:
                return {'success': True, 'output': output.strip(), 'elapsed_time': elapsed_time}
        except Exception as e:
            return {'success': False, 'error': str(e), 'elapsed_time': time.time() - start_time}

    def print_successful_output(self, output, elapsed_time):
        self.console.print(f"[green]✔ Command executed successfully! ({elapsed_time:.2f}s)[/green]")

        lines = output.strip().splitlines()
        if not lines:
            self.console.print("[dim]No output.[/dim]")
            return

        # Attempt to create a table if the output looks tabular
        try:
            headers = lines[0].split()
            if len(lines) > 1 and len(headers) > 1:
                table = Table(show_header=True, header_style="bold magenta", border_style="dim")
                for header in headers:
                    table.add_column(header)

                for line in lines[1:]:
                    table.add_row(*line.split(maxsplit=len(headers)-1))
                self.console.print(table)
            else:
                raise ValueError("Not tabular data")
        except Exception:
            self.console.print(f"[bright_cyan]{output}[/bright_cyan]")

// < app/core/generic_client.py >
import requests
import json
import config

class GenericClient:
    def __init__(self):
        self.base_url = config.HOST
        self.api_key = config.API_KEY
        self.model = config.MODEL
        # --- THIS IS THE FIX ---
        # History is now initialized empty. The system prompt is set by the TaskManager.
        self.history = []
        # --- END OF FIX ---
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def add_user_message(self, content):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, message_dict):
        self.history.append(message_dict)

    def add_tool_response_message(self, tool_call_id, content):
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def purge_chat_history(self):
        # This method is now effectively handled by creating a new client instance
        # but we can leave it for clarity.
        self.history = []

    def get_tool_response(self, tools):
        """
        Gets a standard, non-streaming response. This function ONLY uses 'return'.
        """
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()

            try:
                response_json = response.json()
            except json.JSONDecodeError:
                return {"role": "assistant", "content": "API Error: Received an invalid response from the server."}
            
            if not response_json or 'choices' not in response_json or not response_json['choices']:
                return {"role": "assistant", "content": "API Error: Received an empty or malformed response from the server."}

            return response_json['choices'][0]['message']
        except requests.exceptions.RequestException as e:
            return {"role": "assistant", "content": f"API Connection Error: {e}"}

    def get_streaming_response(self):
        """
        Gets a streaming response. This function ONLY uses 'yield'.
        """
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True
        }
        full_response = ""
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, stream=True, timeout=60)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line[len('data: '):]
                        if json_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(json_str)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                full_response += content
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue
        except requests.exceptions.RequestException as e:
            error_message = f"API Connection Error: {e}"
            full_response = error_message
            yield error_message
        
        self.add_assistant_message({'role': 'assistant', 'content': full_response})

// < app/core/memory.py >
import os
from datetime import datetime

class AgentMemory:
    def __init__(self, filepath='memory.md'):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                f.write("# OConsole Agent Memory\n\n")

    def read(self):
        """Reads the entire content of the memory file."""
        with open(self.filepath, 'r') as f:
            return f.read()

    def append(self, text):
        """Appends a new entry to the memory file with a timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.filepath, 'a') as f:
            f.write(f"## Entry: {timestamp}\n{text}\n\n")

    def clear(self):
        """Wipes the memory file clean."""
        with open(self.filepath, 'w') as f:
            f.write("# OConsole Agent Memory\n\n")

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


// < app/core/tools.py >
import shlex
import config

class ToolExecutor:
    def __init__(self, command_executor):
        self.command_executor = command_executor

    def get_full_system_report(self):
        """
        Gathers a comprehensive system report by running several commands.
        """
        commands = [
            "echo '--- OS and Kernel ---'",
            "uname -a",
            "echo '\n--- Disk Usage ---'",
            "df -h",
            "echo '\n--- System Uptime ---'",
            "uptime"
        ]
        full_report = ""
        for cmd in commands:
            result = self.command_executor.run_command(cmd)
            if result['success']:
                full_report += result['output'] + "\n"
            else:
                full_report += result['error'] + "\n"
        
        return {"success": True, "output": full_report, "elapsed_time": 0}


    def run_safe_command(self, command_name, args_string=""):
        # ... (no change to this function)
        if command_name not in config.SAFE_COMMANDS:
            return {
                "success": False,
                "error": f"Command '{command_name}' is not in the list of approved safe commands."
            }
        
        full_command = f"{command_name} {args_string}"
        return self.command_executor.run_command(full_command)

def get_tools():
    """
    Returns the list of tool definitions for the AI, including the new high-level tool.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_full_system_report",
                "description": "Provides a comprehensive overview of the system, including OS, kernel, disk space, and uptime. Use this for general queries about the system's status.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_safe_command",
                "description": "Executes a specific, pre-approved Linux command for targeted operations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command_name": {
                            "type": "string",
                            "description": "The name of the safe command to execute (e.g., 'ls', 'cat', 'wc').",
                        },
                        "args_string": {
                            "type": "string",
                            "description": "A string containing all the arguments for the command (e.g., '-l /home/user').",
                        },
                    },
                    "required": ["command_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_linux_command",
                "description": "Generates a potentially unsafe or complex command that requires user approval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "A description of the task for which to generate a command.",
                        }
                    },
                    "required": ["task_description"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "answer_question",
                "description": "Provides a conversational answer or a final summary when the user's goal is complete.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The final summary to provide to the user.",
                        }
                    },
                    "required": ["query"],
                },
            },
        },
    ]

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
# Use the 'ollama' provider
PROVIDER=ollama

# Point to the default Ollama server address
HOST=http://localhost:11434/v1

# An API key is not needed for a local Ollama server
API_KEY=

# Specify a model you have downloaded in Ollama that supports tools
MODEL=llama3.1

// < app/.gitignore >
__pycache__/
*.pyc
.env
command_history.txt
.python_history
venv/

// < app/launcher.sh >
#!/bin/bash

# --- Style and Color Definitions ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper function for printing messages ---
step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

echo -e "${GREEN}Starting the AI Assistant Setup & Launch...${NC}"

# 1. Check if we are in the 'app' directory
if [ ! -f "manager.py" ] || [ ! -d "core" ]; then
    echo -e "${YELLOW}Error: Please run this script from inside the 'app' directory that contains 'manager.py'.${NC}"
    exit 1
fi

# 2. Set up the Python virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    step "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Please ensure python3 is installed."
        exit 1
    fi
else
    step "Virtual environment already exists."
fi

# Define Python and Pip executables from the virtual environment
PYTHON_EXEC="$VENV_DIR/bin/python"
PIP_EXEC="$VENV_DIR/bin/pip"

# 3. Install dependencies quietly
step "Installing/verifying required packages..."
$PIP_EXEC install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies from requirements.txt."
    exit 1
fi
echo -e "Dependencies are up to date."

# 4. Configure the environment file (.env)
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    step "Configuration needed: Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}IMPORTANT: The '.env' file has been created."
    echo -e "Please open it in a text editor and set your AI provider (PROVIDER, MODEL, API_KEY, etc.).${NC}"
    read -p "Press [Enter] after you have saved your changes to '.env' to continue..."
else
    step "Configuration file (.env) found."
fi

# 5. Run the main application
step "Launching the AI Command Line Assistant..."
echo -e "${GREEN}--------------------------------------------------${NC}"
$PYTHON_EXEC manager.py

// < app/manager.py >
from core.generic_client import GenericClient
from core.command_executor import CommandExecutor
from core.tools import get_tools, ToolExecutor
from core.memory import AgentMemory
import config
import json

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

class TaskManager:
    def __init__(self):
        self.console = Console()
        self.command_executor = CommandExecutor()
        self.tool_executor = ToolExecutor(self.command_executor)
        self.memory = AgentMemory()
        self.client = None

    def get_planner_client(self):
        client = GenericClient()
        client.history = [{"role": "system", "content": config.PLANNER_SYSTEM_PROMPT}]
        return client

    def get_agent_client(self):
        client = GenericClient()
        client.history = [{"role": "system", "content": config.AGENT_SYSTEM_PROMPT}]
        return client

    def print_welcome(self):
        welcome_panel = Panel(
            "[bold cyan]Welcome to oconsole - AI Agent Mode[/bold cyan]\n\n"
            f"Connected to: [bold green]{config.HOST}[/bold green]\n\n"
            "Enter a complex goal for the agent to achieve.\n"
            "Meta-commands: [yellow]/help, /clear-memory, /exit[/yellow]",
            title="[bold]oconsole[/bold]",
            border_style="magenta"
        )
        self.console.print(welcome_panel)


    def handle_meta_commands(self, user_input):
        if user_input.lower() == '/exit':
            return True
        elif user_input.lower() == '/clear-memory':
            self.memory.clear()
            self.console.print("[bold green]✔ Agent memory cleared.[/bold green]")
            return True
        elif user_input.lower() == '/help':
            self.print_welcome()
            return True
        return False
    
    def get_initial_plan(self, user_goal):
        planner_client = self.get_planner_client()
        planner_client.add_user_message(user_goal)
        
        with self.console.status("[bold green]AI is generating a plan...", spinner="dots"):
            response = planner_client.get_tool_response(tools=None)
        
        content = response.get('content', '')
        try:
            plan_data = json.loads(content)
            if 'is_complex' in plan_data and 'plan' in plan_data:
                return plan_data
            else:
                raise json.JSONDecodeError
        except (json.JSONDecodeError, TypeError):
            self.console.print(Panel("[bold red]Error: The AI planner failed to return a valid plan. Please try rephrasing your goal.[/bold red]"))
            return None

    def render_plan_for_confirmation(self, plan):
        plan_text = Text()
        for i, step in enumerate(plan, 1):
            plan_text.append(f"{i}. {step}\n")
        self.console.print(Panel(plan_text, title="[bold yellow]Proposed Agent Plan[/bold yellow]", border_style="yellow"))

    def confirm_execution(self, prompt_text):
        choice = prompt(prompt_text).lower()
        return choice == 'y'

    def process_task(self, user_goal):
        plan_data = self.get_initial_plan(user_goal)
        if not plan_data:
            return

        if plan_data.get('is_complex', False):
            self.render_plan_for_confirmation(plan_data['plan'])
            if not self.confirm_execution("Approve this plan and start autonomous execution? (y/n): "):
                self.console.print("[bold red]Execution cancelled by user.[/bold red]")
                return
            self.console.print("[bold green]Plan approved! Starting agent...[/bold green]")
        
        self.run_agentic_mode(user_goal, plan_data['plan'])

    def run_agentic_mode(self, user_goal, plan):
        self.client = self.get_agent_client()
        self.memory.clear()
        self.memory.append(f"**Overall Goal:** {user_goal}\n**Execution Plan:**\n" + "\n".join(f"- {s}" for s in plan))

        for i in range(config.AGENT_MAX_STEPS):
            self.console.print(Panel(f"Agent Loop: Step {i+1}/{config.AGENT_MAX_STEPS}", style="bold blue"))
            
            with self.console.status("[bold green]Agent is reasoning...", spinner="dots"):
                memory_context = self.memory.read()
                agent_prompt = f"## Memory & Scratchpad ##\n{memory_context}\n\n## Instruction ##\nBased on your memory and the plan, decide the next immediate action. Choose one tool."
                self.client.add_user_message(agent_prompt)
                
                response_message = self.client.get_tool_response(tools=get_tools())
                self.client.add_assistant_message(response_message)

            tool_calls = response_message.get('tool_calls')

            if not tool_calls or tool_calls[0]['function']['name'] == "answer_question":
                self.console.print("[bold green]Agent has finished the task.[/bold green]")
                summary = "Task completed successfully."
                if tool_calls:
                     arguments = json.loads(tool_calls[0]['function']['arguments'])
                     summary = arguments.get('query', summary)
                self.stream_conversational_response(summary)
                return

            tool_call = tool_calls[0]
            function_name = tool_call['function']['name']
            tool_call_id = tool_call['id']
            try:
                arguments = json.loads(tool_call['function']['arguments'])
                
                # --- THIS IS THE FIX ---
                # Announce the tool and its arguments clearly.
                self.console.print(Panel(f"**Tool:** `[bold cyan]{function_name}[/bold cyan]`\n**Arguments:** {arguments}",
                                       border_style="dim", title="[dim]Agent Action[/dim]"))

                # If it's a command, show the exact command string before running.
                if function_name == 'run_safe_command':
                    command = arguments.get('command_name', '')
                    args = arguments.get('args_string', '')
                    full_command = f"{command} {args}".strip()
                    self.console.print(Panel(f"[bold]$ {full_command}[/bold]", border_style="green", title="[green]Executing Command[/green]"))
                # --- END OF FIX ---
                
                result_output = self.execute_tool(function_name, arguments)
                
                memory_entry = (f"**Action:** Executed tool `{function_name}` with arguments `{arguments}`.\n"
                                f"**Result:**\n```json\n{json.dumps(result_output, indent=2)}\n```")
                self.memory.append(memory_entry)
                self.client.add_tool_response_message(tool_call_id, json.dumps(result_output))

            except json.JSONDecodeError:
                error_msg = "Error: AI generated invalid arguments."
                self.console.print(f"[bold red]{error_msg}[/bold red]")
                self.memory.append(f"**Error:** {error_msg}")

        self.console.print(Panel("[bold yellow]Agent reached maximum steps.[/bold yellow]"))

    def execute_tool(self, function_name, arguments):
        if hasattr(self.tool_executor, function_name):
            method_to_call = getattr(self.tool_executor, function_name)
            return method_to_call(**arguments)
        else:
            return {"success": False, "error": f"Tool '{function_name}' is not a valid direct-execution tool."}

    def stream_conversational_response(self, initial_content=""):
        generated_text = initial_content
        with Live(Markdown(generated_text), console=self.console, refresh_per_second=15, vertical_overflow="visible") as live:
            if initial_content and self.client.history and self.client.history[-1]['role'] == 'assistant':
                 self.client.history.pop()

            for chunk in self.client.get_streaming_response():
                generated_text += chunk
                live.update(Markdown(generated_text))

    def start(self):
        self.print_welcome()
        session_history = FileHistory(config.HISTORY_FILE)
        while True:
            try:
                user_input = prompt(">> ", history=session_history).strip()
                if not user_input:
                    continue
                if self.handle_meta_commands(user_input):
                    if user_input == '/exit':
                        break
                    continue
                self.process_task(user_input)
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[bold red]Exiting...[/bold red]")
                break

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()

// < app/oconsole.sh.example >
source venv/bin/activate; python manager.py


// < app/requirements.txt >
python-dotenv
rich
prompt-toolkit
requests

