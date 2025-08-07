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
    "ps", "netstat"
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