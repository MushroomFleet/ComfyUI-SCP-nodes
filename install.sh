#!/bin/bash

# SaveImageSCP Installation Script for ComfyUI

echo "=================================="
echo "SaveImageSCP Node Installer"
echo "=================================="
echo ""

# Detect ComfyUI directory
if [ -d "../../ComfyUI" ]; then
    COMFYUI_DIR="../../ComfyUI"
elif [ -d "../ComfyUI" ]; then
    COMFYUI_DIR="../ComfyUI"
elif [ -d "ComfyUI" ]; then
    COMFYUI_DIR="ComfyUI"
else
    echo "ComfyUI directory not found!"
    read -p "Enter path to ComfyUI directory: " COMFYUI_DIR
fi

echo "Using ComfyUI directory: $COMFYUI_DIR"
echo ""

# Create custom_nodes directory if it doesn't exist
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes/SaveImageSCP"
mkdir -p "$CUSTOM_NODES_DIR"

# Copy files
echo "Copying files..."
cp SaveImageSCP.py "$CUSTOM_NODES_DIR/"
cp config.json "$CUSTOM_NODES_DIR/"
cp requirements.txt "$CUSTOM_NODES_DIR/"
cp README.md "$CUSTOM_NODES_DIR/"

echo "✓ Files copied to $CUSTOM_NODES_DIR"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "⚠ Warning: Some dependencies may have failed to install"
    echo "  Try running: pip install paramiko python-dotenv"
fi
echo ""

# Create .env template in ComfyUI root
ENV_FILE="$COMFYUI_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env template..."
    cat > "$ENV_FILE" << 'EOF'
# SCP Server Configuration

# Server hostname or IP address
SCP_HOST=your.server.com

# SSH port (default: 22)
SCP_PORT=22

# Username for SSH/SCP authentication
SCP_USERNAME=your_username

# Password for SSH/SCP authentication
SCP_PASSWORD=your_password
EOF
    echo "✓ .env template created at $ENV_FILE"
    echo "  ⚠ IMPORTANT: Edit this file with your actual credentials!"
else
    echo "⚠ .env file already exists, skipping creation"
fi
echo ""

echo "=================================="
echo "Installation Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit $ENV_FILE with your SCP credentials"
echo "2. Edit $CUSTOM_NODES_DIR/config.json to configure profiles"
echo "3. Restart ComfyUI"
echo "4. Look for 'Save Image (SCP Upload)' node in the node menu"
echo ""
echo "For more information, see: $CUSTOM_NODES_DIR/README.md"
