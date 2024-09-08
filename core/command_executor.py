# core/command_executor.py
import subprocess
from colorama import Fore
from tabulate import tabulate

class CommandExecutor:
    def __init__(self):
        pass

    def run_command(self, command):
        """
        Runs a shell command and returns its beautified output or error.
        """
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()

            if process.returncode != 0:
                # Error case: output in red
                print(f"{Fore.RED}Error: {error.decode('utf-8')}")
                return error.decode('utf-8')
            else:
                # Success case: output in green
                output_decoded = output.decode('utf-8')
                print(f"{Fore.GREEN}Command output:")
                lines = output_decoded.split('\n')
                rows = [line.split() for line in lines if line]
                if len(rows) > 1:
                    print(tabulate(rows, headers="firstrow", tablefmt="grid"))
                else:
                    print(output_decoded)
                return output_decoded
        except Exception as e:
            print(f"{Fore.RED}Failed to execute command: {str(e)}")
            return f"Failed to execute command: {str(e)}"
