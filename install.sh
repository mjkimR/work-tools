#!/bin/bash
set -e

# Get the absolute path of the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "Installing work-tools globally via uv..."
echo "=================================================="

if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed."
    echo "Please install uv first (https://github.com/astral-sh/uv)."
    exit 1
fi

# Run uv tool install --editable .
# This installs wt as a global command in uv's managed environment
uv tool install --editable "$REPO_ROOT"

echo ""
echo "=================================================="
echo "Registering work-tools skill globally..."
echo "=================================================="

CONFIG_DIR="$HOME/.gemini/config"
mkdir -p "$CONFIG_DIR"
SKILLS_JSON="$CONFIG_DIR/skills.json"
SKILL_PATH="$REPO_ROOT/.agents/skills"

# Update skills.json using Python to safely handle JSON without tools like jq
python3 -c "
import json, os
path = '$SKILLS_JSON'
new_entry = {'path': '$SKILL_PATH'}
data = {'entries': []}
if os.path.exists(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception:
        pass
if 'entries' not in data:
    data['entries'] = []

# Avoid duplicate entries
if not any(e.get('path') == '$SKILL_PATH' for e in data['entries']):
    data['entries'].append(new_entry)

with open(path, 'w') as f:
    json.dump(data, f, indent=2)
"

echo "Skill registered at: $SKILLS_JSON"
echo ""
echo "=================================================="
echo "SUCCESS: work-tools is installed and registered!"
echo "=================================================="
echo "You can now run 'wt' from any directory, and agents"
echo "will automatically discover and use the work-tools skill."
echo "=================================================="
