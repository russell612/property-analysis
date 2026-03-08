#!/bin/bash
# Property Analysis - Full pipeline: scrape data + rebuild dashboard
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Property Analysis Pipeline ==="
echo "$(date)"

# 1. Install Python dependencies
echo ""
echo "--- Step 1: Installing dependencies ---"
PIP_CMD=""
if command -v pip3 &>/dev/null; then
  PIP_CMD="pip3"
elif command -v pip &>/dev/null; then
  PIP_CMD="pip"
else
  echo "Error: pip not found. Please install Python and pip first."
  exit 1
fi
$PIP_CMD install -r "$SCRIPT_DIR/scraper/requirements.txt" --break-system-packages -q 2>/dev/null || $PIP_CMD install -r "$SCRIPT_DIR/scraper/requirements.txt" -q

# 2. Run the scraper
echo ""
echo "--- Step 2: Scraping property data ---"
cd "$SCRIPT_DIR/scraper"
python3 scrape.py

# 3. Copy data to dashboard public dir
echo ""
echo "--- Step 3: Syncing data to dashboard ---"
mkdir -p "$SCRIPT_DIR/dashboard/public/data"
cp "$SCRIPT_DIR/data/"*.json "$SCRIPT_DIR/dashboard/public/data/" 2>/dev/null || true

# 4. Rebuild dashboard
echo ""
echo "--- Step 4: Building dashboard ---"
cd "$SCRIPT_DIR/dashboard"
# Reinstall node_modules if platform mismatch (e.g. Linux VM vs macOS)
if ! npm run build 2>/dev/null; then
  echo "  Build failed — reinstalling npm dependencies for this platform..."
  rm -rf node_modules package-lock.json
  npm install
  npm run build
fi

# 5. Copy data to dist
echo ""
echo "--- Step 5: Deploying data to dist ---"
mkdir -p "$SCRIPT_DIR/dashboard/dist/data"
cp "$SCRIPT_DIR/data/"*.json "$SCRIPT_DIR/dashboard/dist/data/" 2>/dev/null || true

echo ""
echo "=== Pipeline complete! ==="
echo "Open dashboard/dist/index.html in your browser"
