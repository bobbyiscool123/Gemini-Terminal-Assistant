#!/bin/bash
# install-command.sh - Install the terminal-assistant command globally

# Get the absolute path of the terminal-assistant.sh script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/terminal-assistant.sh"

# Check if the script exists
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Error: terminal-assistant.sh not found at $SCRIPT_PATH"
  exit 1
fi

# Make the script executable if it's not already
chmod +x "$SCRIPT_PATH"

# Create symlink in /usr/local/bin (requires sudo)
echo "Creating symlink in /usr/local/bin..."
if sudo ln -sf "$SCRIPT_PATH" /usr/local/bin/terminal-assistant; then
  echo "✅ Symlink created successfully"
else
  echo "❌ Failed to create symlink (sudo permission denied)"
  echo "Falling back to .bashrc method..."
  
  # Add alias to .bashrc
  BASHRC="$HOME/.bashrc"
  
  # Check if the alias already exists in .bashrc
  if grep -q "alias terminal-assistant=" "$BASHRC"; then
    echo "Alias already exists in $BASHRC. Updating..."
    sed -i "s|alias terminal-assistant=.*|alias terminal-assistant='$SCRIPT_PATH'|" "$BASHRC"
  else
    echo "Adding alias to $BASHRC..."
    echo "" >> "$BASHRC"
    echo "# Terminal Assistant command" >> "$BASHRC"
    echo "alias terminal-assistant='$SCRIPT_PATH'" >> "$BASHRC"
  fi
  
  echo "✅ Added terminal-assistant command to $BASHRC"
  echo "Please run 'source ~/.bashrc' or restart your terminal to apply changes"
fi

echo ""
echo "🎉 Installation complete! You can now use the command anywhere:"
echo "terminal-assistant \"your task here\""
echo "" 