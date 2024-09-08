# core/storage.py
import os

class Storage:
    def __init__(self, history_file="command_history.txt"):
        """
        Initialize the Storage class, setting the history file.
        """
        self.history_file = history_file
        # Ensure the file exists
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as file:
                pass

    def store_command(self, command):
        """
        Append a command to the history file.
        """
        try:
            with open(self.history_file, 'a') as file:
                file.write(command + '\n')
        except Exception as e:
            print(f"Error storing command: {str(e)}")

    def load_history(self):
        """
        Load the history of commands from the file and return them as a list.
        """
        try:
            with open(self.history_file, 'r') as file:
                return [line.strip() for line in file.readlines()]
        except Exception as e:
            print(f"Error loading history: {str(e)}")
            return []

    def clear_history(self):
        """
        Clear the history file.
        """
        try:
            with open(self.history_file, 'w') as file:
                pass
            print("History cleared.")
        except Exception as e:
            print(f"Error clearing history: {str(e)}")
