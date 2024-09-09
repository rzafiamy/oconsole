import subprocess
import pexpect
import time
from colorama import Fore, Style
from tabulate import tabulate

class CommandExecutor:
    def __init__(self):
        pass

    def run_command(self, command, use_pexpect=False, expected_inputs=None):
        """
        Runs a shell command and returns its beautified output or error.
        Handles interactive commands with `pexpect` when `use_pexpect` is True.
        :param command: The shell command to execute.
        :param use_pexpect: Set to True if the command requires interaction.
        :param expected_inputs: A list of dictionaries with 'prompt' and 'response' to handle expected input.
        """
        print(f"{Fore.CYAN}{Style.BRIGHT}Executing command: {Fore.YELLOW}{command}{Style.RESET_ALL}")
        
        start_time = time.time()  # Track execution time
        
        if use_pexpect and expected_inputs:
            return self._run_interactive_command(command, expected_inputs, start_time)
        else:
            return self._run_non_interactive_command(command, start_time)

    def _run_non_interactive_command(self, command, start_time):
        """
        Runs a non-interactive shell command using subprocess.
        """
        try:
            # Start the subprocess
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            output, error = process.communicate()

            # Calculate execution time
            elapsed_time = time.time() - start_time

            if process.returncode != 0:
                # Handle the error case with red output
                print(f"{Fore.RED}{Style.BRIGHT}Error Occurred:{Style.RESET_ALL}")
                print(f"{Fore.RED}{error}{Style.RESET_ALL}")
                print(f"{Fore.RED}{Style.BRIGHT}Execution time: {elapsed_time:.2f} seconds{Style.RESET_ALL}")
                return error
            else:
                # Success case: beautify and format output
                self._print_successful_output(output, elapsed_time)
                return output
        except Exception as e:
            # Catch any unexpected errors and display in red
            print(f"{Fore.RED}Failed to execute command: {str(e)}{Style.RESET_ALL}")
            return str(e)

    def _run_interactive_command(self, command, expected_inputs, start_time):
        """
        Runs an interactive shell command using pexpect and handles expected inputs.
        """
        try:
            # Start the pexpect process
            process = pexpect.spawn(command, encoding='utf-8')

            for input_data in expected_inputs:
                process.expect(input_data['prompt'])  # Wait for the expected prompt
                process.sendline(input_data['response'])  # Send the response

            # Interact and display real-time output
            process.logfile_read = open('command_output.log', 'w')  # Save command output to a log file
            process.interact()

            # Ensure the process completes and capture any remaining output
            process.wait()
            
            elapsed_time = time.time() - start_time
            print(f"{Fore.GREEN}{Style.BRIGHT}Interactive command completed successfully!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Execution time: {elapsed_time:.2f} seconds{Style.RESET_ALL}")

            return True

        except pexpect.exceptions.EOF:
            print(f"{Fore.RED}Command ended unexpectedly (EOF).{Style.RESET_ALL}")
            return False
        
        except pexpect.exceptions.TIMEOUT:
            print(f"{Fore.RED}Command timed out.{Style.RESET_ALL}")
            return False
        
        except Exception as e:
            print(f"{Fore.RED}Failed to execute interactive command: {str(e)}{Style.RESET_ALL}")
            return False

    def _print_successful_output(self, output, elapsed_time):
        """
        Beautify and print the output of a successfully executed command.
        """
        print(f"{Fore.GREEN}{Style.BRIGHT}Command executed successfully!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Execution time: {elapsed_time:.2f} seconds{Style.RESET_ALL}\n")

        # Check if output contains tabular data
        lines = output.splitlines()
        if len(lines) > 1 and all(len(line.split()) > 1 for line in lines):
            rows = [line.split() for line in lines if line]
            headers = rows[0]
            data_rows = rows[1:]
            # Format as a table
            print(tabulate(data_rows, headers=headers, tablefmt="fancy_grid"))
        else:
            # Print plain output
            print(f"{Fore.LIGHTGREEN_EX}{output}{Style.RESET_ALL}")

