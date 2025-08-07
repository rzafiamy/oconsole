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
# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- Connection Settings ---
HOST = os.getenv('HOST', 'http://localhost:11434/v1')
API_KEY = os.getenv('API_KEY')
MODEL = os.getenv('MODEL', 'llama3.1')

# --- Agent Settings ---
AGENT_MAX_STEPS = 7
AGENT_MEMORY_MAX_TOKENS = 16000
SAFE_COMMANDS = [
    "ls", "cat", "echo", "pwd", "df", "du", "wc", "grep",
    "find", "whoami", "uname", "date", "uptime", "journalctl",
    "ps", "netstat", "apt", "dpkg", "mkdir", "touch", "free"
]

# --- App Settings ---
HISTORY_FILE = '.python_history'

AGENT_SYSTEM_PROMPT = f"""
You are oconsole, an expert Linux assistant and a friendly conversational partner. Your primary goal is to help users by executing commands or answering questions.

**Your Workflow & Rules:**

1.  **For simple greetings and conversational chat (like "hello", "what's up?", "thanks"):**
    - Respond directly as a text message without using any tools.
    - Example: User says "thanks". You reply directly with "You're welcome!".

2.  **For tasks requiring system information or file operations:**
    - You MUST use a tool. First, think about which tool to use (`run_safe_command`, `create_file`, etc.).
    - After the tool runs, you MUST use the `answer_question` tool to summarize the result and provide an explanation to the user.

3.  **For general knowledge questions (like "what is a symbolic link?"):**
    - You MUST use the `answer_question` tool to provide a direct answer.

**Summary of Tool Usage:**
- Use `run_safe_command` or other tools to GET information.
- Use `answer_question` to GIVE a final, conclusive answer for a task or question.
- Do NOT use tools for simple chat. Just reply with text.
"""

EXPLAINER_SYSTEM_PROMPT = """You are an expert system assistant. Your role is to interpret the output of a Linux command and provide a brief, one or two-sentence, natural-language explanation for the user. Focus on the most important information in the output. Be concise.
Example Input:
Command: df -h
Output:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   20G   30G  40% /
tmpfs            16G     0   16G   0% /dev/shm
Example Output:
The root filesystem is using 40% of its 50GB capacity, with 30GB of space available.
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
from rich.panel import Panel
from rich.text import Text

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
        """
        Prints the successful output in a styled Panel. If the output looks
        like a table, it's rendered as a rich Table.
        """
        title = f"✔ Success ({elapsed_time:.2f}s)"

        if not output.strip():
            self.console.print(Panel("[dim]No output.[/dim]", title=f"[green]{title}[/green]", border_style="green", title_align="left"))
            return

        lines = output.strip().splitlines()
        
        # Try to render as a table
        try:
            headers = lines[0].split()
            if len(lines) > 1 and len(headers) > 1 and all(len(line.split(maxsplit=len(headers)-1)) == len(headers) for line in lines[1:]):
                table = Table(
                    show_header=True, 
                    header_style="bold cyan", 
                    border_style="dim",
                    title_align="left"
                    )
                for header in headers:
                    table.add_column(header, no_wrap=True)

                for line in lines[1:]:
                    table.add_row(*line.split(maxsplit=len(headers)-1))
                
                panel_content = table

            else:
                raise ValueError("Not tabular data")

        except Exception:
            # Fallback for non-tabular data
            panel_content = Text(output, style="bright_cyan")

        self.console.print(Panel(
            panel_content, 
            title=f"[green]{title}[/green]", 
            border_style="green", 
            title_align="left"
        ))

// < app/core/generic_client.py >
import requests
import json
import config
import tiktoken
import time

class GenericClient:
    def __init__(self):
        self.base_url = config.HOST
        self.api_key = config.API_KEY
        self.model = config.MODEL
        self.history = []
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def get_token_count(self):
        if not self.tokenizer:
            return 0
        
        num_tokens = 0
        for message in self.history:
            num_tokens += len(self.tokenizer.encode(str(message)))
        return num_tokens

    def _prune_history(self):
        if not self.tokenizer or not config.AGENT_MEMORY_MAX_TOKENS:
            return

        while self.get_token_count() > config.AGENT_MEMORY_MAX_TOKENS:
            if len(self.history) > 1:
                self.history.pop(1)
            else:
                break

    def add_user_message(self, content):
        self.history.append({"role": "user", "content": content})
        self._prune_history()

    def add_assistant_message(self, message_dict):
        self.history.append(message_dict)
        self._prune_history()

    def add_tool_response_message(self, tool_call_id, content):
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })
        self._prune_history()

    def purge_chat_history(self):
        self.history = []

    def get_tool_response(self, tools, json_schema=None):
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if json_schema:
            payload["response_format"] = { "type": "json_object" }

        last_error = None
        for attempt in range(3):
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
                last_error = e
                time.sleep(2) # Wait 2 seconds before retrying
        
        return {"role": "assistant", "content": f"API Connection Error: {last_error}"}


    def get_streaming_response(self):
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True
        }
        full_response = ""
        last_error = None
        
        for attempt in range(3):
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
                self.add_assistant_message({'role': 'assistant', 'content': full_response})
                return # Exit the generator successfully
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(2)

        error_message = f"API Connection Error: {last_error}"
        yield error_message
        self.add_assistant_message({'role': 'assistant', 'content': error_message})

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
import os
import time

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
        if command_name not in config.SAFE_COMMANDS:
            return {
                "success": False,
                "error": f"Command '{command_name}' is not in the list of approved safe commands."
            }
        
        full_command = f"{command_name} {args_string}"
        return self.command_executor.run_command(full_command)

    def create_file(self, file_path, content):
        """
        Creates a new file at the specified path and writes content to it.
        This is the safest method for file creation.
        """
        start_time = time.time()
        try:
            # --- THE FIX ---
            # Expand the '~' character to the user's home directory path
            expanded_path = os.path.expanduser(file_path)
            
            # Use the expanded path for all operations
            parent_dir = os.path.dirname(expanded_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(expanded_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            elapsed_time = time.time() - start_time
            return {
                "success": True, 
                "output": f"Successfully created file: {expanded_path}", # Return the resolved path
                "elapsed_time": elapsed_time
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Failed to create file {file_path}. Error: {str(e)}",
                "elapsed_time": elapsed_time
            }


def get_tools():
    """
    Returns the list of tool definitions for the AI, including the new high-level tool.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Creates or overwrites a file with specified content. Use this for creating any new file, especially for code, HTML, or multi-line text. This is the only safe and reliable way to create files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The relative or absolute path for the new file (e.g., 'src/index.js' or '~/Documents/project/main.py').",
                        },
                        "content": {
                            "type": "string",
                            "description": "The complete content to be written to the file. This can be multi-line.",
                        },
                    },
                    "required": ["file_path", "content"],
                },
            },
        },
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
                "description": "Executes a specific, pre-approved Linux command for targeted operations. Do NOT use this to create files; use the 'create_file' tool instead.",
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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- ASCII Art Banner ---
echo -e "${CYAN}"
cat << "EOF"
  ____  _                              
 / __ \(_)___  ____  ___  ____ ___  ___ 
/ / / / / __ \/ __ \/ _ \/ __ `__ \/ _ \
/ /_/ / / / / / / / /  __/ / / / / /  __/
\____/_/_/ /_/_/ /_/\___/_/ /_/ /_/\___/ 
             AI Command Assistant      
EOF
echo -e "${NC}"


# --- Helper function for printing messages ---
step() {
    echo -e "\n${BLUE}➜${NC} ${YELLOW}$1${NC}"
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
    step "Creating Python virtual environment in './$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Please ensure python3 is installed."
        exit 1
    fi
else
    step "Virtual environment found."
fi

# Define Python and Pip executables from the virtual environment
PYTHON_EXEC="$VENV_DIR/bin/python"
PIP_EXEC="$VENV_DIR/bin/pip"

# 3. Install dependencies quietly
step "Installing/verifying required packages..."
$PIP_EXEC install -r requirements.txt --quiet --disable-pip-version-check
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
    echo -e "Please open it and set your AI provider details (MODEL, API_KEY, etc.).${NC}"
    read -p "Press [Enter] after you have saved your changes to '.env' to continue..."
else
    step "Configuration file (.env) found."
fi

# 5. Run the main application
step "Launching oconsole..."
echo -e "${GREEN}--------------------------------------------------${NC}"
$PYTHON_EXEC manager.py

// < app/manager.py >
from core.generic_client import GenericClient
from core.command_executor import CommandExecutor
from core.tools import get_tools, ToolExecutor
from core.memory import AgentMemory
import config
import json
import os

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.rule import Rule

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

class TaskManager:
    def __init__(self):
        self.console = Console()
        self.command_executor = CommandExecutor()
        self.tool_executor = ToolExecutor(self.command_executor)
        self.memory = AgentMemory()
        self.client = None
        self.last_answer = ""
        self.last_command_info = None
        self.history = FileHistory(config.HISTORY_FILE)
        self.memory.clear()

    def get_agent_client(self):
        client = GenericClient()
        client.history = [{"role": "system", "content": config.AGENT_SYSTEM_PROMPT}]
        return client

    def print_welcome(self):
        logo = Text("oconsole", style="bold magenta")
        tagline = Text("Your Autonomous AI Command Assistant", style="cyan")
        
        info_grid = Table.grid(padding=(0, 2))
        info_grid.add_column(style="green")
        info_grid.add_column()
        info_grid.add_row("✓ Model:", config.MODEL)
        info_grid.add_row("✓ Endpoint:", config.HOST)
        info_grid.add_row("✓ Max Memory:", f"{config.AGENT_MEMORY_MAX_TOKENS:,} tokens")
        
        main_panel_content = Table.grid(expand=True)
        main_panel_content.add_row(Align.center(logo))
        main_panel_content.add_row(Align.center(tagline))
        main_panel_content.add_row("")
        main_panel_content.add_row(Align.center(info_grid))
        main_panel_content.add_row("")
        main_panel_content.add_row(Align.center(Text("Ask a question, state a goal, or type /help for commands.", style="yellow")))

        welcome_panel = Panel(
            main_panel_content,
            title="[bold]Welcome[/bold]",
            border_style="dim",
            padding=(1, 2)
        )
        self.console.print(welcome_panel)

    def _get_explanation(self, command, output):
        explainer_client = GenericClient()
        explainer_client.history = [{"role": "system", "content": config.EXPLAINER_SYSTEM_PROMPT}]
        prompt = f"Command: {command}\nOutput:\n{output}"
        explainer_client.add_user_message(prompt)
        
        with self.console.status("[bold green]AI is generating an explanation...", spinner="dots"):
            response = explainer_client.get_tool_response(tools=None)
        
        return response.get('content', 'Could not generate explanation.')

    def handle_meta_commands(self, user_input):
        parts = user_input.split()
        command = parts[0].lower()

        if command == '/exit':
            return "exit"

        elif command in ['/new', '/clear-memory']:
            self.memory.clear()
            self.last_answer = ""
            self.last_command_info = None
            if self.client:
                self.client = self.get_agent_client()
            self.console.print(Panel("[bold green]✔ New session started. Agent memory has been cleared.[/bold green]", border_style="green", width=70))
            return "handled"

        elif command in ['/cls', '/clear-screen']:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_welcome()
            return "handled"

        elif command == '/help':
            help_text = """
[bold]Meta-Commands:[/bold]
  [cyan]/help[/cyan]                 - Show this help message.
  [cyan]/new[/cyan] or [cyan]/clear-memory[/cyan]  - Start a new session, clearing memory.
  [cyan]/exit[/cyan]                 - Exit oconsole.
  [cyan]/cls[/cyan] or [cyan]/clear-screen[/cyan]  - Clear the console screen.

[bold]Inspection Commands:[/bold]
  [cyan]/params[/cyan]               - Show current configuration parameters (model, endpoint, etc.).
  [cyan]/model[/cyan]                - Show the current AI model.
  [cyan]/endpoint[/cyan]             - Show the current API endpoint.
  [cyan]/system[/cyan]               - Display the agent's system prompt.
  [cyan]/tools[/cyan]                - List all available tools for the agent.
  [cyan]/memory[/cyan]               - Display the raw memory log for the last task.

[bold]Utility Commands:[/bold]
  [cyan]/last[/cyan]                 - Re-run the last prompt.
  [cyan]/explain[/cyan]              - Explain the output of the last command executed.
  [cyan]/save <filename>[/cyan]   - Save the agent's last final answer to a file.

[bold]Usage:[/bold]
  Simply type your goal or question and press Enter. The AI agent will handle the rest.
"""
            self.console.print(Panel(help_text, title="[bold magenta]oconsole Help[/bold magenta]", border_style="magenta"))
            return "handled"

        elif command == '/model':
            self.console.print(Panel(config.MODEL, title="[cyan]Current Model[/cyan]", border_style="cyan"))
            return "handled"

        elif command == '/endpoint':
            self.console.print(Panel(config.HOST, title="[cyan]Current Endpoint[/cyan]", border_style="cyan"))
            return "handled"

        elif command == '/system':
            self.console.print(Panel(Markdown(config.AGENT_SYSTEM_PROMPT), title="[cyan]Agent System Prompt[/cyan]", border_style="cyan"))
            return "handled"
            
        elif command == '/params':
            grid = Table.grid(padding=(0, 2))
            grid.add_column(style="green", justify="right")
            grid.add_column()
            grid.add_row("Model:", config.MODEL)
            grid.add_row("Endpoint:", config.HOST)
            grid.add_row("Max Memory Tokens:", f"{config.AGENT_MEMORY_MAX_TOKENS:,}")
            grid.add_row("Max Agent Steps:", str(config.AGENT_MAX_STEPS))
            self.console.print(Panel(grid, title="[cyan]Configuration Parameters[/cyan]", border_style="cyan"))
            return "handled"

        elif command == '/memory':
            self.console.print(Panel(self.memory.read(), title="[cyan]Agent Memory Log[/cyan]", border_style="cyan", expand=False))
            return "handled"

        elif command == '/tools':
            tools_list = get_tools()
            table = Table(title="[cyan]Available Agent Tools[/cyan]", border_style="cyan", show_header=True, header_style="bold magenta")
            table.add_column("Name", style="dim", no_wrap=True)
            table.add_column("Description")
            for tool in tools_list:
                func = tool.get('function', {})
                table.add_row(func.get('name'), func.get('description'))
            self.console.print(table)
            return "handled"

        elif command == '/save':
            if len(parts) < 2:
                self.console.print("[bold red]Error: Please provide a filename. Usage: /save <filename>[/bold red]")
                return "handled"
            if not self.last_answer:
                self.console.print("[bold yellow]No previous answer to save.[/bold yellow]")
                return "handled"
            
            filename = " ".join(parts[1:])
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.last_answer)
                self.console.print(Panel(f"✔ Answer saved to [cyan]{os.path.abspath(filename)}[/cyan]", border_style="green"))
            except Exception as e:
                self.console.print(f"[bold red]Error saving file: {e}[/bold red]")
            return "handled"

        elif command == '/last':
            try:
                all_prompts = self.history.get_strings()
                if not all_prompts: raise IndexError
                last_prompt = all_prompts[-1]
                if last_prompt.lower().split()[0].startswith('/'):
                     self.console.print("[bold yellow]Cannot re-run a meta-command.[/bold yellow]")
                     return "handled"
                self.console.print(f"› [dim]Re-running last prompt:[/] [bright_cyan]{last_prompt}[/bright_cyan]")
                return last_prompt
            except IndexError:
                self.console.print("[bold yellow]No history found.[/bold yellow]")
                return "handled"
        
        elif command == '/explain':
            if not self.last_command_info:
                self.console.print("[bold yellow]No recent command output to explain. Run a command first.[/bold yellow]")
                return "handled"
            
            explanation = self._get_explanation(
                self.last_command_info['command'],
                self.last_command_info['output']
            )
            
            explanation_panel = Panel(
                Text(explanation, style="italic bright_white"),
                title=f"[bold blue]💡 Explanation for: `{self.last_command_info['command']}`[/bold blue]",
                border_style="blue"
            )
            self.console.print(explanation_panel)
            return "handled"

        return "unhandled"

    def process_task(self, user_goal):
        self.run_agentic_mode(user_goal)

    def run_agentic_mode(self, user_goal):
        self.client = self.get_agent_client()
        self.memory.clear()
        
        self.client.add_user_message(user_goal)

        for i in range(config.AGENT_MAX_STEPS):
            token_status = f"Memory: {self.client.get_token_count():,}/{config.AGENT_MEMORY_MAX_TOKENS:,} Tokens"
            self.console.print(Rule(f"[bold blue]Agent Step {i+1}/{config.AGENT_MAX_STEPS}[/bold blue] | [yellow]{token_status}[/yellow]", style="blue"))
            
            with self.console.status("[bold green]Agent is reasoning...", spinner="dots"):
                response_message = self.client.get_tool_response(tools=get_tools())
                self.client.add_assistant_message(response_message)

            if response_message.get('content'):
                self.console.print("[bold green]✔ Agent Replied[/bold green]")
                self.display_final_answer(response_message['content'])
                return

            tool_calls = response_message.get('tool_calls')

            if not tool_calls:
                self.console.print("[bold yellow]Agent finished without providing an answer or action.[/bold yellow]")
                return

            tool_call = tool_calls[0]
            function_name = tool_call['function']['name']
            tool_call_id = tool_call['id']
            
            try:
                arguments = json.loads(tool_call['function']['arguments'])
                
                action_table = Table.grid(padding=(0, 1))
                action_table.add_column(style="dim"); action_table.add_column()
                action_table.add_row("Tool:", f"[bold cyan]{function_name}[/bold cyan]")
                action_table.add_row("Arguments:", f"[cyan]{json.dumps(arguments, indent=2)}[/cyan]")
                self.console.print(Panel(action_table, title="[bold dim]Agent Action[/bold dim]", border_style="dim"))

                if function_name == "answer_question":
                    self.console.print("[bold green]✔ Agent has finished the task.[/bold green]")
                    summary = arguments.get('query', "Task completed successfully.")
                    self.display_final_answer(summary)
                    return

                if function_name == 'run_safe_command':
                    self.console.print(Panel(f"$ {arguments.get('command_name', '')} {arguments.get('args_string', '')}".strip(), 
                                             border_style="green", title="[green]Executing Command[/green]", title_align="left"))
                
                result_output = self.execute_tool(function_name, arguments)
                
                if function_name in ['run_safe_command', 'get_full_system_report', 'create_file']:
                    if result_output.get('success'):
                        self.command_executor.print_successful_output(result_output['output'], result_output['elapsed_time'])
                        if function_name == 'run_safe_command' and result_output.get('output'):
                             full_command = f"{arguments.get('command_name', '')} {arguments.get('args_string', '')}".strip()
                             self.last_command_info = {'command': full_command, 'output': result_output['output']}
                        else:
                             self.last_command_info = None
                    else:
                        self.console.print(Panel(Text(result_output.get('error', 'An unknown error occurred.'), style="red"), title="[red]✖ Command Failed[/red]", border_style="red"))
                        self.last_command_info = None

                self.client.add_tool_response_message(tool_call_id, json.dumps(result_output))
                self.console.print()

            except (json.JSONDecodeError, TypeError):
                error_msg = f"Error: AI generated invalid arguments for {function_name}."
                self.console.print(f"[bold red]{error_msg}[/bold red]")
                self.client.add_tool_response_message(tool_call_id, json.dumps({"success": False, "error": error_msg}))

        self.console.print(Panel("[bold yellow]Agent reached maximum steps and could not complete the task.[/bold yellow]", border_style="yellow"))

    def execute_tool(self, function_name, arguments):
        if hasattr(self.tool_executor, function_name):
            return getattr(self.tool_executor, function_name)(**arguments)
        return {"success": False, "error": f"Tool '{function_name}' is not valid."}

    def display_final_answer(self, final_answer=""):
        self.last_answer = final_answer
        self.console.print(Panel(Markdown(final_answer, style="bright_green"),
            title="[bold magenta]Final Answer[/bold magenta]", border_style="magenta", padding=(1, 2)))

    def start(self):
        self.print_welcome()
        while True:
            try:
                user_input = prompt("› ", history=self.history).strip()
                if not user_input:
                    continue
                
                self.console.print()
                command_result = self.handle_meta_commands(user_input)

                if command_result == "exit":
                    self.console.print("[bold red]Exiting...[/bold red]")
                    break
                elif command_result == "handled":
                    self.console.print()
                    continue
                elif command_result != "unhandled":
                    self.process_task(command_result)
                else:
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
tiktoken

