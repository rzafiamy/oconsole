from core.generic_client import GenericClient
from core.command_executor import CommandExecutor
from core import tools
import config
import os
import json

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

class TaskManager:
    def __init__(self):
        self.console = Console()
        self.client = GenericClient()  # <-- The only change needed here!
        self.command_executor = CommandExecutor()

    def print_welcome(self):
        welcome_panel = Panel(
            "[bold cyan]Welcome to oconsole - Your AI Command-Line Assistant[/bold cyan]\n\n"
            f"Connected to: [bold green]{config.HOST}[/bold green]\n"
            f"Model: [bold green]{config.MODEL}[/bold green]\n\n"
            "Type a command, ask a question, or use a meta-command:\n"
            "  • [bold yellow]/help[/bold yellow] - Show this help message\n"
            "  • [bold yellow]/clear[/bold yellow] - Clear the conversation history\n"
            "  • [bold yellow]/exit[/bold yellow] - Exit the application",
            title="[bold]oconsole[/bold]",
            border_style="magenta"
        )
        self.console.print(welcome_panel)

    def handle_meta_commands(self, user_input):
        if user_input.lower() == '/exit':
            self.console.print("[bold red]Exiting...[/bold red]")
            return True
        elif user_input.lower() == '/clear':
            self.client.purge_chat_history()
            self.console.print("[bold green]✔ Conversation history cleared.[/bold green]")
            return True
        elif user_input.lower() == '/help':
            self.print_welcome()
            return True
        return False

    def process_task(self, user_input):
        self.client.add_user_message(user_input)

        with self.console.status("[bold green]AI is thinking...", spinner="dots") as status:
            tool_definitions = tools.get_tools()
            response_message = self.client.get_tool_response(tools=tool_definitions)
            self.client.add_assistant_message(response_message)
            
            tool_calls = response_message.get('tool_calls')

            if not tool_calls:
                status.stop()
                self.stream_conversational_response()
                return

            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                arguments = json.loads(tool_call['function']['arguments'])

                if function_name == "generate_linux_command":
                    status.update("[bold green]Generating commands...")
                    task = arguments.get('task_description', '')
                    prompt = f"Generate only the raw linux command(s) for this task: {task}. Do not include explanations, backticks, or any other text."
                    
                    self.client.add_user_message(prompt)
                    commands_str = ""
                    for chunk in self.client.get_streaming_response():
                        commands_str += chunk

                    commands = [cmd.strip() for cmd in commands_str.splitlines() if cmd.strip()]
                    
                    status.stop()
                    self.render_command_plan(commands)
                    if commands and self.confirm_execution():
                        self.execute_commands(commands)

                elif function_name == "answer_question":
                    status.stop()
                    self.stream_conversational_response()

    def render_command_plan(self, commands):
        command_text = "\n".join(f"{i+1}. {cmd}" for i, cmd in enumerate(commands))
        plan_panel = Panel(
            command_text,
            title="[bold yellow]Generated Command Plan[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        self.console.print(plan_panel)

    def confirm_execution(self):
        choice = prompt("Execute this plan? (y/n): ").lower()
        return choice == 'y'

    def execute_commands(self, commands):
        for command in commands:
            self.console.print(f"\n[dim]Executing: {command}[/dim]")
            result = self.command_executor.run_command(command)
            if result['success']:
                self.command_executor.print_successful_output(result['output'], result['elapsed_time'])
            else:
                self.console.print(Panel(f"[bold red]Error[/bold red]: {result['error']}", border_style="red"))

    def stream_conversational_response(self):
        # The user's query and the assistant's tool-less response are already in history.
        # We pop the assistant's preliminary (non-streamed) response to replace it with a streamed one.
        if self.client.history and self.client.history[-1]['role'] == 'assistant':
            self.client.history.pop()

        generated_text = ""
        with Live(console=self.console, refresh_per_second=15) as live:
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