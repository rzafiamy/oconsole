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