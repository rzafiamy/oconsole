# core/ui_helpers.py
from halo import Halo
from colorama import Fore, Style
from tqdm import tqdm
import time

class UIHelpers:
    def __init__(self):
        pass

    def start_spinner(self, text):
        spinner = Halo(text=text, spinner='dots')
        spinner.start()
        return spinner

    def stop_spinner(self, spinner, success=True, message=""):
        if success:
            spinner.succeed(message)
        else:
            spinner.fail(message)

    def display_progress_bar(self, duration=2, steps=10):
        with tqdm(total=100, desc="Running command", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
            for _ in range(steps):
                pbar.update(100 // steps)
                time.sleep(duration / steps)

    def confirm_execution(self, command):
        print(f"{Fore.CYAN}Generated command: {Style.BRIGHT}{command}")
        return input(f"{Fore.YELLOW}Do you want to run this command? (y/n): ").lower() == 'y'

    def show_final_output(self, output):
        print(f"{Fore.BLUE}Final command output:\n{output}")
