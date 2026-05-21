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

# ---------------------------------------------------------------------------
# Sync host's global Claude Code configuration (if available)
# ---------------------------------------------------------------------------
sync_host_claude_config() {
    local HOST_CONFIG="/host-claude-config"
    local USER_CONFIG="$HOME/.claude"

    if [ ! -d "$HOST_CONFIG" ] || [ -z "$(ls -A "$HOST_CONFIG" 2>/dev/null)" ]; then
        echo "No host Claude config found, skipping sync"
        return 0
    fi

    echo "Syncing host Claude Code configuration..."
    mkdir -p "$USER_CONFIG"

    # Copy portable single files
    for file in CLAUDE.md keybindings.json; do
        if [ -f "$HOST_CONFIG/$file" ]; then
            echo "  Copying $file"
            cp "$HOST_CONFIG/$file" "$USER_CONFIG/$file"
        fi
    done

    # Copy portable directories
    for dir in agents commands skills; do
        if [ -d "$HOST_CONFIG/$dir" ] && [ -n "$(ls -A "$HOST_CONFIG/$dir" 2>/dev/null)" ]; then
            echo "  Copying $dir/"
            cp -r "$HOST_CONFIG/$dir" "$USER_CONFIG/"
        fi
    done

    # Copy plugins (selective — skip marketplaces which are ~300MB of git repos)
    if [ -d "$HOST_CONFIG/plugins" ]; then
        echo "  Syncing plugins..."
        mkdir -p "$USER_CONFIG/plugins"

        # Copy small metadata files
        for file in config.json blocklist.json; do
            if [ -f "$HOST_CONFIG/plugins/$file" ]; then
                cp "$HOST_CONFIG/plugins/$file" "$USER_CONFIG/plugins/$file"
            fi
        done

        # Copy and rewrite installed_plugins.json (fix host-specific paths)
        if [ -f "$HOST_CONFIG/plugins/installed_plugins.json" ]; then
            node -e "
                const fs = require('fs');
                const data = JSON.parse(fs.readFileSync('$HOST_CONFIG/plugins/installed_plugins.json', 'utf8'));
                if (data.plugins) {
                    for (const entries of Object.values(data.plugins)) {
                        for (const entry of entries) {
                            if (entry.installPath) {
                                entry.installPath = entry.installPath.replace(/^\/home\/[^/]+\/.claude/, '$USER_CONFIG');
                            }
                        }
                    }
                }
                fs.writeFileSync('$USER_CONFIG/plugins/installed_plugins.json', JSON.stringify(data, null, 2));
            "
        fi

        # Copy and rewrite known_marketplaces.json (fix host-specific paths)
        if [ -f "$HOST_CONFIG/plugins/known_marketplaces.json" ]; then
            node -e "
                const fs = require('fs');
                const data = JSON.parse(fs.readFileSync('$HOST_CONFIG/plugins/known_marketplaces.json', 'utf8'));
                for (const marketplace of Object.values(data)) {
                    if (marketplace.installLocation) {
                        marketplace.installLocation = marketplace.installLocation.replace(/^\/home\/[^/]+\/.claude/, '$USER_CONFIG');
                    }
                }
                fs.writeFileSync('$USER_CONFIG/plugins/known_marketplaces.json', JSON.stringify(data, null, 2));
            "
        fi

        # Copy plugin subdirectories (cache and local plugins, skip large marketplaces)
        for dir in cache local data; do
            if [ -d "$HOST_CONFIG/plugins/$dir" ] && [ -n "$(ls -A "$HOST_CONFIG/plugins/$dir" 2>/dev/null)" ]; then
                echo "    Copying plugins/$dir/"
                cp -r "$HOST_CONFIG/plugins/$dir" "$USER_CONFIG/plugins/"
            fi
        done
    fi

    echo "Host config sync complete."
}

sync_host_claude_config

# ---------------------------------------------------------------------------
# Configure MCP servers
# ---------------------------------------------------------------------------
if command -v claude &>/dev/null; then
    echo "Configuring Chrome DevTools MCP server..."
    claude mcp remove chrome-devtools 2>/dev/null || true
    claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest
else
    echo "WARNING: claude CLI not found, skipping MCP configuration"
fi

# ---------------------------------------------------------------------------
# Merge settings.json (host settings + container overrides)
# ---------------------------------------------------------------------------
echo "Configuring settings.json..."
mkdir -p ~/.claude
SETTINGS_FILE="$HOME/.claude/settings.json"
HOST_SETTINGS="/host-claude-config/settings.json"

node -e "
    const fs = require('fs');
    let settings = {};

    // Layer 1: Host settings (portable subset)
    if (fs.existsSync('$HOST_SETTINGS')) {
        try {
            settings = JSON.parse(fs.readFileSync('$HOST_SETTINGS', 'utf8'));
            // Remove keys that reference host-specific file paths
            delete settings.hooks;
            delete settings.statusLine;
            console.log('  Merged host settings.json');
        } catch (e) {
            console.error('  WARNING: Failed to parse host settings.json:', e.message);
            settings = {};
        }
    }

    // Layer 2: Existing container settings (from previous setup/rebuild)
    if (fs.existsSync('$SETTINGS_FILE')) {
        try {
            const existing = JSON.parse(fs.readFileSync('$SETTINGS_FILE', 'utf8'));
            settings = { ...settings, ...existing };
            console.log('  Merged existing container settings.json');
        } catch (e) {
            console.error('  WARNING: Failed to parse existing settings.json:', e.message);
        }
    }

    // Layer 3: Container-required settings
    settings.preferRemoteControl = true;

    fs.writeFileSync('$SETTINGS_FILE', JSON.stringify(settings, null, 2));
    console.log('  Wrote merged settings.json');
"

echo "Claude Code setup complete."
