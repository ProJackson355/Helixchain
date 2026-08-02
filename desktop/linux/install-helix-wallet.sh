#!/usr/bin/env sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/192x192/apps"
mkdir -p "$BIN_DIR" "$APP_DIR" "$ICON_DIR"
cp "$HERE/helix-wallet" "$BIN_DIR/helix-wallet"
chmod +x "$BIN_DIR/helix-wallet"
sed "s|^Exec=.*|Exec=$BIN_DIR/helix-wallet|" \
  "$HERE/helix-wallet.desktop" > "$APP_DIR/helix-wallet.desktop"
cp "$HERE/helix-logo.png" "$ICON_DIR/helix-wallet.png"
printf '%s\n' "Helix Wallet was installed. If it does not appear immediately, sign out and back in."
