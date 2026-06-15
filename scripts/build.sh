#!/bin/bash
# Build script: PyInstaller onefile for mimir-memory Executa
# Bundles mimir binary inside the package so it's self-contained.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BUILD_DIR="$ROOT/build/dist"
mkdir -p "$BUILD_DIR"

MIMIR_SRC="/opt/data/webui/minions/.minions-data/mimir/mimir"
PLUGIN="$ROOT/executas/mimir-memory/mimir_memory_plugin.py"
OUTPUT_NAME="mimir-memory"
MIMIR_BUNDLE="$ROOT/executas/mimir-memory/mimir"

echo "=== Building $OUTPUT_NAME ==="
echo "Root: $ROOT"

# 1. Copy mimir into executa dir for bundling
cp "$MIMIR_SRC" "$MIMIR_BUNDLE"
chmod +x "$MIMIR_BUNDLE"

# 2. Build with PyInstaller
pyinstaller \
    --onefile \
    --name "$OUTPUT_NAME" \
    --add-data "$MIMIR_BUNDLE:." \
    --distpath "$BUILD_DIR" \
    --workpath "$ROOT/build/pyinstaller-work" \
    --specpath "$ROOT/build" \
    --clean \
    "$PLUGIN"

echo ""
echo "=== Build complete ==="
echo "Binary: $BUILD_DIR/$OUTPUT_NAME"
ls -lh "$BUILD_DIR/$OUTPUT_NAME"

# 3. Test
echo ""
echo "=== Smoke test ==="
echo '{"jsonrpc":"2.0","id":1,"method":"describe"}' | timeout 15 "$BUILD_DIR/$OUTPUT_NAME" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'describe: {d[\"result\"][\"name\"]} — {len(d[\"result\"][\"tools\"])} tools')" 2>&1 || echo "WARNING: describe failed (expected if mimir needs PATH)"

# Clean up
rm -f "$MIMIR_BUNDLE"

echo ""
echo "=== Done ==="
