#!/bin/bash
# Forge CLI Installer
# Quick install script for Ubuntu servers

set -e

echo "🔧 Installing Forge CLI..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Run: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION detected"

# Create installation directory
INSTALL_DIR="$HOME/.forge"
mkdir -p "$INSTALL_DIR"

# Clone or update repository
if [ -d "$INSTALL_DIR/forge-cli" ]; then
    echo "📥 Updating Forge..."
    cd "$INSTALL_DIR/forge-cli"
    git pull origin main
else
    echo "📥 Downloading Forge..."
    git clone git@github.com:boparaiamrit/forge-cli.git "$INSTALL_DIR/forge-cli"
    cd "$INSTALL_DIR/forge-cli"
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Reinstall the package (force reinstall to pick up new modules)
echo "📦 Installing Forge CLI package..."
pip uninstall forge-cli -y 2>/dev/null || true
pip install -e . --quiet

# Create wrapper script instead of symlink
# This ensures proper PYTHONPATH is set
FORGE_BIN="/usr/local/bin/forge"
WRAPPER_SCRIPT="$INSTALL_DIR/forge-cli/forge-wrapper.sh"

cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.forge/forge-cli"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"
python -m cli "$@"
EOF

chmod +x "$WRAPPER_SCRIPT"

# Remove old symlink/file and create new one
if [ -L "$FORGE_BIN" ] || [ -f "$FORGE_BIN" ]; then
    sudo rm "$FORGE_BIN"
fi

echo "🔗 Creating forge command..."
sudo ln -s "$WRAPPER_SCRIPT" "$FORGE_BIN"

echo ""
echo "✅ Forge CLI installed successfully!"
echo ""
echo "   Run 'forge' to start."
echo ""

