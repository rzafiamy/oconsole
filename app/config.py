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

# --- NEW, SIMPLIFIED AND MORE FORCEFUL PROMPT ---
AGENT_SYSTEM_PROMPT = f"""
You are a task-oriented AI assistant. Your only purpose is to accomplish the user's request by executing a series of commands. You MUST follow these steps in order, without exception:

1.  **PLAN:** Your first action is ALWAYS to call the `explain_plan` tool to state your step-by-step plan. Do not use any other tool first.

2.  **EXECUTE:** After planning, use the `run_safe_command` or `create_file` tools to execute the steps from your plan.

3.  **ANSWER:** Once the task is fully complete, and only then, you MUST call the `answer_question` tool with the final summary for the user.

Do not deviate from this workflow. Do not engage in conversation.

**Critical Instruction for a known issue:** For the user request "what time is it?", your first step is to generate a plan to use the `date` command.
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