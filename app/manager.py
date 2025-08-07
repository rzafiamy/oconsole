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