import os
from datetime import datetime

class AgentMemory:
    def __init__(self, filepath='memory.md'):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                f.write("# OConsole Agent Memory\n\n")

    def read(self):
        """Reads the entire content of the memory file."""
        with open(self.filepath, 'r') as f:
            return f.read()

    def append(self, text):
        """Appends a new entry to the memory file with a timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.filepath, 'a') as f:
            f.write(f"## Entry: {timestamp}\n{text}\n\n")

    def clear(self):
        """Wipes the memory file clean."""
        with open(self.filepath, 'w') as f:
            f.write("# OConsole Agent Memory\n\n")