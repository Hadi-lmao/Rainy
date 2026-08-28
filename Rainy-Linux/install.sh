#!/bin/bash

APP_NAME="Rainy"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DESKTOP_FILE="$HOME/.local/share/applications/rainy.desktop"

echo "Installing Rainy..."

mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.local/share/applications"

cp -r ./* "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/Rainy"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Rainy
Comment=Pomodoro Timer
Exec=$INSTALL_DIR/Rainy
Icon=$INSTALL_DIR/icon.png
Terminal=false
Type=Application
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

echo "Rainy has been installed!"
echo "You can find it in your application launcher. Also, Aarav is gay"
