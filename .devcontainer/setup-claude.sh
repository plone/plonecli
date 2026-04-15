#!/bin/bash
set -euo pipefail

# Claude Code and OpenCode are installed into the image via the Dockerfile.
# This script only handles per-container configuration that depends on the
# mounted ~/.claude volume.

export PATH="$HOME/.local/bin:$PATH"

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
