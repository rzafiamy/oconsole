# app/manager.py
from core.generic_client import GenericClient
from core.command_executor import CommandExecutor
from core.tools import get_tools, ToolExecutor
from core.memory import AgentMemory
import config
import json
import os
import tiktoken

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
        self.client = GenericClient()
        self.last_answer = ""
        self.last_command_info = None
        self.history = FileHistory(config.HISTORY_FILE)
        
        # --- NEW: Persistent conversation history ---
        self.conversation_history = []
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None
        
        self.memory.clear()

    def _prune_history(self):
        """Keeps the conversation history within the token limit."""
        if not self.tokenizer or not config.AGENT_MEMORY_MAX_TOKENS:
            return

        token_count = 0
        for message in self.conversation_history:
            token_count += len(self.tokenizer.encode(str(message.get("content", ""))))

        # Remove oldest messages (after the first user message) until token count is acceptable
        while token_count > config.AGENT_MEMORY_MAX_TOKENS:
            if len(self.conversation_history) > 2: # Always keep at least one user/assistant exchange
                removed_message = self.conversation_history.pop(1) # Remove the second oldest message
                token_count -= len(self.tokenizer.encode(str(removed_message.get("content", ""))))
            else:
                break # Stop if we can't prune further

    def _add_to_history(self, message):
        """Adds a message to the history and prunes if necessary."""
        self.conversation_history.append(message)
        self._prune_history()

    def print_welcome(self):
        logo = Text("oconsole", style="bold magenta")
        tagline = Text("Your Programmatic AI Command Assistant", style="cyan")
        
        info_grid = Table.grid(padding=(0, 2))
        info_grid.add_column(style="green")
        info_grid.add_column()
        info_grid.add_row("✓ Model:", config.MODEL)
        info_grid.add_row("✓ Endpoint:", config.HOST)
        info_grid.add_row("✓ Agent Mode:", "Programmatic (Conversational)")
        
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
        prompt_messages = [
            {"role": "system", "content": config.EXPLAINER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: {command}\nOutput:\n{output}"}
        ]
        
        with self.console.status("[bold green]AI is generating an explanation...", spinner="dots"):
            response = explainer_client.get_tool_response(messages=prompt_messages, tools=None)
        
        return response.get('content', 'Could not generate explanation.')

    def handle_meta_commands(self, user_input):
        parts = user_input.split()
        command = parts[0].lower()

        if command == '/exit':
            return "exit"
        
        elif command in ['/new', '/clear-memory']:
            self.conversation_history = [] # Clear the persistent history
            self.console.print(Panel("[bold green]✔ New session started. Conversational memory has been cleared.[/bold green]", border_style="green", width=70))
            return "handled"

        elif command in ['/cls', '/clear-screen']:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_welcome()
            return "handled"

        # ... (rest of meta commands are unchanged) ...
        elif command == '/help':
            help_text = """
[bold]Meta-Commands:[/bold]
  [cyan]/help[/cyan]                 - Show this help message.
  [cyan]/new[/cyan] or [cyan]/clear-memory[/cyan]  - Start a new session, clearing conversational memory.
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
        
        elif command == '/system':
            self.console.print(Panel(json.dumps(config.STATE_PROMPTS, indent=2), title="[cyan]Agent State Prompts[/cyan]", border_style="cyan"))
            return "handled"
            
        elif command == '/model':
            self.console.print(Panel(config.MODEL, title="[cyan]Current Model[/cyan]", border_style="cyan"))
            return "handled"

        elif command == '/endpoint':
            self.console.print(Panel(config.HOST, title="[cyan]Current Endpoint[/cyan]", border_style="cyan"))
            return "handled"

        elif command == '/params':
            grid = Table.grid(padding=(0, 2))
            grid.add_column(style="green", justify="right")
            grid.add_column()
            grid.add_row("Model:", config.MODEL)
            grid.add_row("Endpoint:", config.HOST)
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
        self._add_to_history({"role": "user", "content": user_goal})
        self.run_agentic_mode()

    def run_agentic_mode(self):
        current_state = "PLANNING"

        for i in range(config.AGENT_MAX_STEPS):
            token_count = sum(len(self.tokenizer.encode(str(m.get("content", "")))) for m in self.conversation_history) if self.tokenizer else 0
            self.console.print(Rule(f"[bold blue]Step {i+1}/{config.AGENT_MAX_STEPS} | State: {current_state} | History: {token_count} Tokens[/bold blue]", style="blue"))

            system_prompt = config.STATE_PROMPTS[current_state]
            messages_for_api = [{"role": "system", "content": system_prompt}] + self.conversation_history
            
            with self.console.status("[bold green]Agent is processing...", spinner="dots"):
                response_message = self.client.get_tool_response(messages=messages_for_api, tools=get_tools())
            
            self._add_to_history(response_message)

            if response_message.get('content'):
                self.console.print("[bold green]✔ Agent Replied Directly[/bold green]")
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

                # Display logic
                if function_name == "explain_plan":
                    plan_text = arguments.get('plan', 'No plan provided.')
                    self.console.print(Panel(Text(plan_text, style="italic yellow"), title="[bold blue]🤔 Agent's Plan[/bold blue]", border_style="blue"))
                else:
                    action_table = Table.grid(padding=(0, 1))
                    action_table.add_column(style="dim"); action_table.add_column()
                    action_table.add_row("Tool:", f"[bold cyan]{function_name}[/bold cyan]")
                    action_table.add_row("Arguments:", f"[cyan]{json.dumps(arguments, indent=2)}[/cyan]")
                    self.console.print(Panel(action_table, title="[bold dim]Agent Action[/bold dim]", border_style="dim"))

                if function_name == 'run_safe_command':
                    self.console.print(Panel(f"$ {arguments.get('command_name', '')} {arguments.get('args_string', '')}".strip(), border_style="green", title="[green]Executing Command[/green]", title_align="left"))

                result_output = self.execute_tool(function_name, arguments)

                if function_name not in ['explain_plan', 'answer_question']:
                    if result_output.get('success'):
                        self.command_executor.print_successful_output(result_output['output'], result_output['elapsed_time'])
                        if function_name == 'run_safe_command' and result_output.get('output'):
                             self.last_command_info = {'command': f"{arguments.get('command_name', '')} {arguments.get('args_string', '')}".strip(), 'output': result_output['output']}
                        else:
                             self.last_command_info = None
                    else:
                        self.console.print(Panel(Text(result_output.get('error', 'An unknown error occurred.'), style="red"), title="[red]✖ Command Failed[/red]", border_style="red"))
                        self.last_command_info = None
                
                tool_response_content = json.dumps(result_output)
                self._add_to_history({"role": "tool", "tool_call_id": tool_call_id, "content": tool_response_content})
                
                if current_state == "PLANNING" and function_name == "explain_plan":
                    current_state = "EXECUTING"
                elif function_name == "answer_question":
                    self.console.print("[bold green]✔ Agent has finished the task.[/bold green]")
                    self.display_final_answer(arguments.get('query', "Task completed."))
                    return
                
                self.console.print()

            except (json.JSONDecodeError, TypeError) as e:
                error_msg = f"Error processing tool call: {e}"
                self.console.print(f"[bold red]{error_msg}[/bold red]")
                self._add_to_history({"role": "tool", "tool_call_id": tool_call_id, "content": json.dumps({"success": False, "error": error_msg})})

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
                    # This logic is now simpler
                    self.process_task(command_result)
                else:
                    self.process_task(user_input)
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[bold red]Exiting...[/bold red]")
                break

if __name__ == "__main__":
    manager = TaskManager()
    manager.start()