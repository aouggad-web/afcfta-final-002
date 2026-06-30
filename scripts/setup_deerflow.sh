#!/usr/bin/env bash
# setup_deerflow.sh — Clone and initialize DeerFlow local development environment.
# Follows https://raw.githubusercontent.com/bytedance/deer-flow/main/Install.md
# Idempotent: safe to re-run.

set -euo pipefail

DEERFLOW_REPO="https://github.com/bytedance/deer-flow.git"
DEERFLOW_DIR="${DEERFLOW_DIR:-$HOME/deer-flow}"

echo "================================================="
echo "  DeerFlow — Setup script"
echo "  Target directory: $DEERFLOW_DIR"
echo "================================================="

# Step 1: Clone if not already present
if [ -d "$DEERFLOW_DIR/.git" ]; then
  echo "✓ DeerFlow already cloned at $DEERFLOW_DIR — skipping clone."
else
  echo "→ Cloning DeerFlow..."
  git clone "$DEERFLOW_REPO" "$DEERFLOW_DIR"
  echo "✓ Cloned."
fi

cd "$DEERFLOW_DIR"

# Step 2: Verify repo structure
for required in Makefile backend frontend config.example.yaml; do
  if [ ! -e "$required" ]; then
    echo "✗ Missing expected file/directory: $required"
    echo "  The clone may be incomplete. Remove $DEERFLOW_DIR and re-run."
    exit 1
  fi
done
echo "✓ Repo structure verified."

# Step 3: Create config.yaml if it does not exist
if [ -f config.yaml ]; then
  echo "✓ config.yaml already exists — skipping make config."
else
  echo "→ Generating config.yaml..."
  make config
  echo "✓ config.yaml created."
fi

# Step 4: Choose setup path — Docker preferred
if docker info >/dev/null 2>&1; then
  echo "→ Docker is available. Running make docker-init..."
  make docker-init
  echo ""
  echo "================================================="
  echo "  Setup complete — Docker path"
  echo "================================================="
  echo "  Files created : config.yaml"
  echo "  Next command  : make docker-start"
  echo ""
  echo "  ⚠  No LLM model is configured yet."
  echo "     Open config.yaml and uncomment (or add) at least one"
  echo "     entry under 'models:'. Common options:"
  echo "       - OpenAI   → set OPENAI_API_KEY and uncomment gpt-4 block"
  echo "       - Anthropic → set ANTHROPIC_API_KEY and uncomment claude block"
  echo "       - Ollama   → uncomment the Ollama section (no key needed)"
  echo "================================================="
else
  echo "→ Docker not available. Running make check..."
  make check
  echo "→ Running make install..."
  make install
  echo ""
  echo "================================================="
  echo "  Setup complete — Local path"
  echo "================================================="
  echo "  Files created : config.yaml"
  echo "  Next command  : make dev"
  echo ""
  echo "  ⚠  No LLM model is configured yet."
  echo "     Open config.yaml and uncomment (or add) at least one"
  echo "     entry under 'models:'. Common options:"
  echo "       - OpenAI   → set OPENAI_API_KEY and uncomment gpt-4 block"
  echo "       - Anthropic → set ANTHROPIC_API_KEY and uncomment claude block"
  echo "       - Ollama   → uncomment the Ollama section (no key needed)"
  echo "================================================="
fi
