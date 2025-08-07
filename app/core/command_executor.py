import subprocess
import time
from rich.console import Console
from rich.table import Table

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
        self.console.print(f"[green]✔ Command executed successfully! ({elapsed_time:.2f}s)[/green]")

        lines = output.strip().splitlines()
        if not lines:
            self.console.print("[dim]No output.[/dim]")
            return

        # Attempt to create a table if the output looks tabular
        try:
            headers = lines[0].split()
            if len(lines) > 1 and len(headers) > 1:
                table = Table(show_header=True, header_style="bold magenta", border_style="dim")
                for header in headers:
                    table.add_column(header)

                for line in lines[1:]:
                    table.add_row(*line.split(maxsplit=len(headers)-1))
                self.console.print(table)
            else:
                raise ValueError("Not tabular data")
        except Exception:
            self.console.print(f"[bright_cyan]{output}[/bright_cyan]")