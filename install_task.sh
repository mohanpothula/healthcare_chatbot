#!/bin/bash
# AI Task Manager installer — Ubuntu on AWS EC2
set -e

echo ""
echo "=== AI Task Manager Installer ==="
echo ""

# 1. System packages
echo "[1/4] Updating apt and installing python3-pip..."
sudo apt-get update -q
sudo apt-get install -y -q python3 python3-pip

# 2. Python packages
echo "[2/4] Installing Python packages..."
pip3 install anthropic rich --break-system-packages

# 3. Place script
echo "[3/4] Installing task.py to ~/bin..."
mkdir -p ~/bin
cp task.py ~/bin/task.py
chmod +x ~/bin/task.py

cat > ~/bin/task <<'EOF'
#!/bin/bash
python3 ~/bin/task.py "$@"
EOF
chmod +x ~/bin/task

# 4. PATH
if ! echo "$PATH" | grep -q "$HOME/bin"; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi

# 5. API key prompt
echo ""
echo "[4/4] Almost done!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Set your Anthropic API key to enable AI:"
echo ""
echo "  echo 'export ANTHROPIC_API_KEY=sk-...' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo ""
echo "  Get a free key at: https://console.anthropic.com"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Commands (after: source ~/.bashrc):"
echo '  task add "call dentist tomorrow afternoon"'
echo '  task add "finish report by friday, urgent"'
echo "  task list"
echo "  task pending"
echo "  task overdue"
echo "  task done <id>"
echo '  task ask "what should I focus on today?"'
echo ""
