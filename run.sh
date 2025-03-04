#!/bin/bash

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Check if virtual environment exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install project in development mode
echo "Installing project and dependencies..."
uv pip install -e ".[dev]"

# Check if .env file exists, if not create from example
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file and add your API keys"
    exit 1
fi

# Run the Streamlit application
echo "Starting AI Debate Club application..."
streamlit run app.py
