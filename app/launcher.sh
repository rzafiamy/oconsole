#!/bin/bash

# --- Style and Color Definitions ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper function for printing messages ---
step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

echo -e "${GREEN}Starting the AI Assistant Setup & Launch...${NC}"

# 1. Check if we are in the 'app' directory
if [ ! -f "manager.py" ] || [ ! -d "core" ]; then
    echo -e "${YELLOW}Error: Please run this script from inside the 'app' directory that contains 'manager.py'.${NC}"
    exit 1
fi

# 2. Set up the Python virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    step "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Please ensure python3 is installed."
        exit 1
    fi
else
    step "Virtual environment already exists."
fi

# Define Python and Pip executables from the virtual environment
PYTHON_EXEC="$VENV_DIR/bin/python"
PIP_EXEC="$VENV_DIR/bin/pip"

# 3. Install dependencies quietly
step "Installing/verifying required packages..."
$PIP_EXEC install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies from requirements.txt."
    exit 1
fi
echo -e "Dependencies are up to date."

# 4. Configure the environment file (.env)
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    step "Configuration needed: Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}IMPORTANT: The '.env' file has been created."
    echo -e "Please open it in a text editor and set your AI provider (PROVIDER, MODEL, API_KEY, etc.).${NC}"
    read -p "Press [Enter] after you have saved your changes to '.env' to continue..."
else
    step "Configuration file (.env) found."
fi

# 5. Run the main application
step "Launching the AI Command Line Assistant..."
echo -e "${GREEN}--------------------------------------------------${NC}"
$PYTHON_EXEC manager.py