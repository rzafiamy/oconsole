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

    def get_planner_client(self):
        client = GenericClient()
        client.history = [{"role": "system", "content": config.PLANNER_SYSTEM_PROMPT}]
        return client

    def get_agent_client(self):
        client = GenericClient()
        client.history = [{"role": "system", "content": config.AGENT_SYSTEM_PROMPT}]
        return client

    def print_welcome(self):
        """Prints a more professional and stylish welcome message."""
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
        main_panel_content.add_row(Align.center(Text("Enter a goal for the agent, or type /help for commands.", style="yellow")))

        welcome_panel = Panel(
            main_panel_content,
            title="[bold]Welcome[/bold]",
            border_style="dim",
            padding=(1, 2)
        )
        self.console.print(welcome_panel)

    def handle_meta_commands(self, user_input):
        """Handles meta-commands with styled feedback."""
        if user_input.lower() == '/exit':
            return True
        elif user_input.lower() == '/clear-memory':
            self.memory.clear()
            if self.client:
                # Re-initialize the agent client to clear its history as well
                self.client = self.get_agent_client()
            self.console.print(Panel("[bold green]✔ Agent memory and chat history have been cleared.[/bold green]", border_style="green", width=60))
            return True
        elif user_input.lower() == '/help':
            help_text = """
[bold]Meta-Commands:[/bold]
  [cyan]/help[/cyan]          - Show this help message.
  [cyan]/clear-memory[/cyan] - Clear the agent's short-term memory and chat history for the next task.
  [cyan]/exit[/cyan]          - Exit oconsole.

[bold]Usage:[/bold]
  Simply type your goal and press Enter. The AI will formulate a plan and, upon your approval, execute it.
  
  [italic]Example: "Find all text files in my home directory and count the total number of lines."[/italic]
"""
            self.console.print(Panel(Markdown(help_text), title="[bold magenta]oconsole Help[/bold magenta]", border_style="magenta"))
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
            self.console.print(Panel("[bold red]Error: The AI planner failed to return a valid JSON plan.[/bold red]\n[yellow]This can happen if the model is not suitable for JSON-forced output or if the request was ambiguous. Please try rephrasing your goal.[/yellow]",
            title="[bold red]Planning Failure[/bold red]", border_style="red"))
            return None

    def render_plan_for_confirmation(self, plan):
        """Renders the proposed plan in a more visually appealing panel."""
        plan_text = Text()
        for i, step in enumerate(plan, 1):
            plan_text.append(f"[cyan]{i}.[/cyan] {step}\n")
        
        self.console.print(
            Panel(
                plan_text, 
                title="[yellow]🤖 Proposed Agent Plan[/yellow]", 
                border_style="yellow",
                subtitle="Review the steps below."
            )
        )

    def confirm_execution(self, prompt_text):
        choice = prompt(f"› {prompt_text} (y/n): ").lower()
        return choice == 'y'

    def process_task(self, user_goal):
        plan_data = self.get_initial_plan(user_goal)
        if not plan_data:
            return

        if plan_data.get('is_complex', False):
            self.render_plan_for_confirmation(plan_data['plan'])
            if not self.confirm_execution("Approve this plan and start autonomous execution?"):
                self.console.print("[bold red]Execution cancelled by user.[/bold red]")
                return
            self.console.print("[bold green]✔ Plan approved! Starting agent...[/bold green]\n")
        
        self.run_agentic_mode(user_goal, plan_data['plan'])

    def run_agentic_mode(self, user_goal, plan):
        self.client = self.get_agent_client()
        self.memory.clear()
        self.memory.append(f"**Overall Goal:** {user_goal}\n**Execution Plan:**\n" + "\n".join(f"- {s}" for s in plan))

        for i in range(config.AGENT_MAX_STEPS):
            current_tokens = self.client.get_token_count()
            token_status = f"Memory: {current_tokens:,}/{config.AGENT_MEMORY_MAX_TOKENS:,} Tokens"
            self.console.print(Rule(f"[bold blue]Agent Step {i+1}/{config.AGENT_MAX_STEPS}[/bold blue] | [yellow]{token_status}[/yellow]", style="blue"))
            
            with self.console.status("[bold green]Agent is reasoning...", spinner="dots"):
                memory_context = self.memory.read()
                agent_prompt = f"## Memory & Scratchpad ##\n{memory_context}\n\n## Instruction ##\nBased on your memory and the plan, decide the next immediate action. Choose one tool."
                self.client.add_user_message(agent_prompt)
                
                response_message = self.client.get_tool_response(tools=get_tools())
                self.client.add_assistant_message(response_message)

            tool_calls = response_message.get('tool_calls')

            if not tool_calls or tool_calls[0]['function']['name'] == "answer_question":
                self.console.print("[bold green]✔ Agent has finished the task.[/bold green]")
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
                
                action_table = Table.grid(padding=(0, 1))
                action_table.add_column(style="dim")
                action_table.add_column()
                action_table.add_row("Tool:", f"[bold cyan]{function_name}[/bold cyan]")
                args_str = json.dumps(arguments, indent=2)
                action_table.add_row("Arguments:", f"[cyan]{args_str}[/cyan]")
                
                self.console.print(
                    Panel(action_table, title="[bold dim]Agent Action[/bold dim]", border_style="dim")
                )
                
                if function_name == 'run_safe_command':
                    command = arguments.get('command_name', '')
                    args = arguments.get('args_string', '')
                    full_command = f"{command} {args}".strip()
                    self.console.print(Panel(f"$ {full_command}", border_style="green", title="[green]Executing Command[/green]", title_align="left"))
                
                result_output = self.execute_tool(function_name, arguments)
                
                if function_name in ['run_safe_command', 'get_full_system_report']:
                    if result_output.get('success'):
                        self.command_executor.print_successful_output(result_output['output'], result_output['elapsed_time'])
                    else:
                        self.console.print(Panel(Text(result_output.get('error', 'An unknown error occurred.'), style="red"), title="[red]✖ Command Failed[/red]", border_style="red"))

                memory_entry = (f"**Action:** Executed tool `{function_name}` with arguments `{arguments}`.\n"
                                f"**Result:**\n```json\n{json.dumps(result_output, indent=2)}\n```")
                self.memory.append(memory_entry)
                self.client.add_tool_response_message(tool_call_id, json.dumps(result_output))
                self.console.print()

            except json.JSONDecodeError:
                error_msg = "Error: AI generated invalid arguments."
                self.console.print(f"[bold red]{error_msg}[/bold red]")
                self.memory.append(f"**Error:** {error_msg}")

        self.console.print(Panel("[bold yellow]Agent reached maximum steps.[/bold yellow]", border_style="yellow"))

    def execute_tool(self, function_name, arguments):
        if hasattr(self.tool_executor, function_name):
            method_to_call = getattr(self.tool_executor, function_name)
            return method_to_call(**arguments)
        else:
            return {"success": False, "error": f"Tool '{function_name}' is not a valid direct-execution tool."}

    def stream_conversational_response(self, initial_content=""):
        full_response = initial_content
        
        live_panel = Panel(
            Markdown(full_response),
            title="[bold magenta]Final Answer[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        )

        with Live(live_panel, console=self.console, refresh_per_second=15, vertical_overflow="visible") as live:
            if initial_content and self.client.history and self.client.history[-1]['role'] == 'assistant':
                 self.client.history.pop()

            for chunk in self.client.get_streaming_response():
                full_response += chunk
                live.update(Panel(
                    Markdown(full_response, style="bright_green"),
                    title="[bold magenta]Final Answer[/bold magenta]",
                    border_style="magenta",
                    padding=(1, 2)
                ))

    def start(self):
        self.print_welcome()
        session_history = FileHistory(config.HISTORY_FILE)
        while True:
            try:
                user_input = prompt("› ", history=session_history).strip()
                if not user_input:
                    continue
                self.console.print()
                if self.handle_meta_commands(user_input):
                    if user_input == '/exit':
                        break
                    self.console.print()
                    continue
                self.process_task(user_input)
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[bold red]Exiting...[/bold red]")
                break

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()