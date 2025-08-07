# app/core/tools.py
import shlex
import config
import os
import time

class ToolExecutor:
    def __init__(self, command_executor):
        self.command_executor = command_executor

    def explain_plan(self, plan):
        """
        Presents the AI's step-by-step plan to the user before execution.
        """
        # This tool's logic is primarily handled in the manager, which will print the plan.
        # Here, we just return the plan as the successful output.
        return {"success": True, "output": plan, "elapsed_time": 0}

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
            expanded_path = os.path.expanduser(file_path)
            
            parent_dir = os.path.dirname(expanded_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(expanded_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            elapsed_time = time.time() - start_time
            return {
                "success": True, 
                "output": f"Successfully created file: {expanded_path}",
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
    Returns the list of tool definitions for the AI, including the new explain_plan tool.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "explain_plan",
                "description": "Outlines the step-by-step plan for the user before executing any actions. This should be the first tool called for any multi-step task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "string",
                            "description": "A clear, user-friendly explanation of the steps the AI will take to achieve the user's goal.",
                        },
                    },
                    "required": ["plan"],
                },
            },
        },
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