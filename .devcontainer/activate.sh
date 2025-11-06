#!/bin/bash
# Hive Builder environment setup script
# Source this file or add it to your ~/.bashrc

# Add Poetry to PATH
export PATH="/home/vscode/.local/bin:$PATH"

# Add Poetry venv to PATH if it exists
if [ -d "/workspaces/hive-builder/.venv/bin" ]; then
    export PATH="/workspaces/hive-builder/.venv/bin:$PATH"
fi

# Alias for hive command
alias hive='poetry run hive'

# Show welcome message only once per session
if [ -z "$HIVE_BUILDER_ENV_LOADED" ]; then
    export HIVE_BUILDER_ENV_LOADED=1
    echo "🐝 Hive Builder environment loaded!"
    echo "   Use: hive --help"
fi
