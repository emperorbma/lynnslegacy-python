#!/usr/bin/env bash
# Fetch Lynn's Legacy 1.1 Linux Full from SourceForge for gameplay comparison.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${REF_GAME_DIR:-$ROOT/ref/ll-1.1-linux}"
CACHE="${REF_GAME_CACHE:-$ROOT/ref/cache}"
SF_URL="${REF_GAME_URL:-https://sourceforge.net/projects/lynn/files/Lynn_s%20Legacy%201.1/Linux%20Full/ll-linux.7z/download}"
FMOD_URL="${REF_FMOD_URL:-https://zdoom.org/files/fmod/fmodapi375linux.tar.gz}"

mkdir -p "$CACHE" "$DEST"
ARCHIVE="$CACHE/ll-linux.7z"
FMOD_TGZ="$CACHE/fmodapi375linux.tar.gz"

if [[ ! -f "$ARCHIVE" ]]; then
  echo "Downloading ll-linux.7z ..."
  curl -L --fail --retry 3 -o "$ARCHIVE" "$SF_URL"
fi

if [[ ! -f "$FMOD_TGZ" ]]; then
  echo "Downloading FMOD 3.75 (libfmod.so) ..."
  curl -L --fail --retry 3 -o "$FMOD_TGZ" "$FMOD_URL"
fi

echo "Extracting into $DEST ..."
rm -rf "$DEST"
mkdir -p "$DEST"
# Prefer system 7z; fall back to Python py7zr.
if command -v 7z >/dev/null 2>&1; then
  7z x -y "$ARCHIVE" -o"$DEST" >/dev/null
else
  python3 - <<PY
import py7zr
from pathlib import Path
with py7zr.SevenZipFile(r"""$ARCHIVE""", mode="r") as z:
    z.extractall(path=Path(r"""$DEST"""))
PY
fi

tar -xzf "$FMOD_TGZ" -C "$CACHE"
cp "$CACHE/fmodapi375linux/api/libfmod-3.75.so" "$DEST/libfmod.so"
chmod +x "$DEST/ll-linux-full" "$DEST/config" 2>/dev/null || true

cat > "$DEST/.ref_game_ready" <<EOF
source=sourceforge
archive=ll-linux.7z
fmod=libfmod-3.75.so
EOF

echo "Ready: $DEST/ll-linux-full"
echo "Run with: tools/ref_game/run.sh"
