# 🖥️ Oconsole

**Oconsole** is an interactive Python-based tool powered by Ollama's LLaMA model to automate Linux command-line operations. The tool uses natural language to generate Linux commands and executes them with a smooth and intuitive interface, providing command history storage for persistent session management.

## 🚀 Features

- 🌐 **Natural Language Processing (NLP)** to convert task descriptions into Linux commands using the LLaMA model.
- 💾 **Persistent Command History**: Automatically store every executed command and retrieve them across sessions.
- 🌀 **Progress Spinners** and **Progress Bars** to visualize execution.
- 🛠️ **Command Confirmation**: Verify before running any generated commands.
- 📜 **Beautifully Formatted Output**: Commands are displayed with table formatting where applicable.
- 📂 **History Management**: Load and review your previous commands with a simple command.

---

## 📋 Table of Contents

- [Installation](#installation)
- [How to Use](#how-to-use)
- [Configuration](#configuration)
- [Command History](#command-history)
- [Example](#example)
- [Contributing](#contributing)

---

## 💻 Installation

### Prerequisites

- 🐍 **Python 3.8+**
- 🛠️ **Pip**: Python's package manager
- 🌐 **Ollama** API: To interact with the LLaMA model, ensure you have access to the Ollama API. 

### Steps

1. **Clone the repository**:

    ```bash
    git clone https://github.com/rzafiamy/Oconsole.git
    cd Oconsole
    ```

2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up the environment** (if necessary):
   
   You might need to configure your `OLLAMA_API_KEY` in an environment variable:

    ```bash
    export OLLAMA_API_KEY="your_api_key_here"
    ```

---

## 📝 How to Use

1. **Run the application**:

    ```bash
    python manager.py
    ```

2. **Interactive Mode**:
   
   Oconsole will start in interactive mode. Simply describe the task you want to automate in natural language.

    ```bash
    Describe the task (or type 'exit' to quit, 'history' to view command history): 
    ```

3. **Confirmation**:

   Oconsole will generate a Linux command and ask for your confirmation before executing it:

    ```bash
    Do you want to run this command? (y/n): 
    ```

---

## ⚙️ Configuration

You can configure Oconsole via the `config.py` file:

```python
# config.py

OLLAMA_MODEL = 'llama3.1:latest'  # Specify the LLaMA model version
OLLAMA_MAX_TOKENS = 50            # Maximum number of tokens to be used by the model
OLLAMA_TEMPERATURE = 0.5          # Temperature for LLM response randomness
HISTORY_FILE = 'command_history.txt' # Path to store command history
```

You can adjust:
- The LLaMA model version
- Token limits
- Temperature for response randomness
- Command history file path

---

## 📜 Command History

Oconsole provides a simple yet powerful command history feature that allows you to:
- **Automatically store** every executed command.
- **Review the command history** by typing `history` during the interactive session.
- **Clear the history** (optional, feature to be added).

### View Command History

During an interactive session, simply type:

```bash
history
```

You'll see a list of previously executed commands with their index.

---

## 📚 Example

Here’s a full example of how Oconsole works:

```bash
$ python manager.py
🟣 Welcome to the Python LLM-powered command interpreter!
💡 Describe the task (or type 'exit' to quit, 'history' to view command history): List all files in the /home directory

💡 Generated command: ls /home
❓ Do you want to run this command? (y/n): y

Running command | ████████████████████████████████████████████████| 100/100 [00:02]
🟢 Command output:
  ----------------
  | file1 | file2 |
  ----------------

💡 Describe the task (or type 'exit' to quit, 'history' to view command history): history
🟣 Command History:
1. ls /home
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a new Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎉 Acknowledgements

Thanks to Ollama for their amazing API, and to the open-source community for the tools used in this project, including:

- [Ollama API](https://ollama.com/)
- [Colorama](https://pypi.org/project/colorama/)
- [TQDM](https://tqdm.github.io/)
- [Tabulate](https://pypi.org/project/tabulate/)
- [Halo](https://pypi.org/project/halo/)

---

## 🧠 AI-Powered Linux Automation

**Oconsole** simplifies your Linux operations by allowing you to run commands with the power of AI. Simply describe what you want to do, and let Oconsole handle the rest! 🎉
