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

# --- STATE MACHINE PROMPTS ---
# This replaces the single AGENT_SYSTEM_PROMPT with a strict, state-based system.
STATE_PROMPTS = {
    "PLANNING": """
You are in the PLANNING state.
Your ONLY valid action is to call the `explain_plan` tool.
Analyze the user's goal and create a step-by-step plan.
Do not use any other tool. Your response must be a call to `explain_plan`.
""",
    "EXECUTING": """
You are in the EXECUTING state.
Your goal is to execute the steps from the user's approved plan.
Review the history to see the original plan and what has already been done.
Your valid actions are:
1. Call `run_safe_command` or `create_file` to perform the NEXT step in the plan.
2. If all steps are complete, call `answer_question` to finish the task.

Do not call `explain_plan` again. Stick to the original plan.
"""
}

# The explainer prompt remains for the /explain command
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