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