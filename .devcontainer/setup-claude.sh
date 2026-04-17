#!/bin/bash
set -euo pipefail

# Ensure ~/.local/bin exists and is on PATH
mkdir -p "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Installing Claude Code (native)..."
if curl -fsSL -o "$TMPDIR/claude-install.sh" https://claude.ai/install.sh; then
    bash "$TMPDIR/claude-install.sh"
else
    echo "WARNING: Failed to download Claude Code installer, skipping"
fi

echo "Installing OpenCode..."
if curl -fsSL -o "$TMPDIR/opencode-install.sh" https://opencode.ai/install; then
    bash "$TMPDIR/opencode-install.sh"
else
    echo "WARNING: Failed to download OpenCode installer, skipping"
fi

if command -v claude &>/dev/null; then
    echo "Configuring Chrome DevTools MCP server..."
    claude mcp remove chrome-devtools 2>/dev/null || true
    claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest
else
    echo "WARNING: claude CLI not found, skipping MCP configuration"
fi

echo "Enabling remote control for all sessions..."
mkdir -p ~/.claude
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
  # Merge preferRemoteControl into existing settings using node (available in the container)
  node -e "
    const fs = require('fs');
    const s = JSON.parse(fs.readFileSync('$SETTINGS_FILE', 'utf8'));
    s.preferRemoteControl = true;
    fs.writeFileSync('$SETTINGS_FILE', JSON.stringify(s, null, 2));
  "
else
  echo '{"preferRemoteControl": true}' > "$SETTINGS_FILE"
fi

echo "Claude Code and OpenCode setup complete."
