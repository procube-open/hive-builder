#!/bin/bash
set -e

echo "🚀 Setting up Hive Builder development environment..."

# Install Poetry
echo "📦 Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/home/vscode/.local/bin:$PATH"

# Configure Poetry to create virtual environments in the project
poetry config virtualenvs.in-project true

# Install project dependencies
echo "📚 Installing Python dependencies..."
poetry install --no-interaction

# Install Ansible collections
echo "🎭 Installing Ansible collections..."
poetry run ansible-galaxy collection install -r hive_builder/requirements.yml

# Install additional system packages for cloud providers
echo "☁️ Installing cloud provider CLI tools..."
sudo apt-get update

sudo apt-get install -y sshpass

# # AWS CLI (if not already installed)
# if ! command -v aws &> /dev/null; then
#     echo "Installing AWS CLI..."
#     sudo apt-get install -y awscli
# fi

# # Azure CLI
# if ! command -v az &> /dev/null; then
#     echo "Installing Azure CLI..."
#     curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
# fi

# # Google Cloud SDK
# if ! command -v gcloud &> /dev/null; then
#     echo "Installing Google Cloud SDK..."
#     # Create keyring directory if it doesn't exist
#     sudo mkdir -p /usr/share/keyrings
#     # Download and add the Google Cloud public key
#     curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
#     # Add the gcloud CLI distribution URI as a package source
#     echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
#     # Update and install the gcloud CLI
#     sudo apt-get update && sudo apt-get install -y google-cloud-sdk
# fi

# Set up bash completion for hive command
echo "⚙️ Setting up bash completion..."

# Add environment activation to bashrc
echo "" >> ~/.bashrc
echo "# Hive Builder environment" >> ~/.bashrc
echo "if [ -f /workspaces/hive-builder/.devcontainer/activate.sh ]; then" >> ~/.bashrc
echo "    source /workspaces/hive-builder/.devcontainer/activate.sh" >> ~/.bashrc
echo "fi" >> ~/.bashrc

if [ -f hive_builder/hive-completion.sh ]; then
    echo "" >> ~/.bashrc
    echo "# Hive Builder completion" >> ~/.bashrc
    echo "source /workspaces/hive-builder/hive_builder/hive-completion.sh" >> ~/.bashrc
fi

# Make scripts executable
chmod +x hive_builder/hive.py
chmod +x .devcontainer/activate.sh

echo "✅ Setup complete! You can now use the 'hive' command directly:"
echo "   hive --help"
echo ""
echo "Or with poetry explicitly:"
echo "   poetry run hive --help"
echo ""
echo "To activate the virtual environment:"
echo "   poetry shell"
