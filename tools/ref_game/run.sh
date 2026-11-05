#!/usr/bin/env bash
# Launch the fetched 1.1 Linux reference binary for side-by-side gameplay.
#
# Needs: i386 libs (libc6:i386, libX11, libXext, libXpm, libXrandr, libXrender,
# libncurses5:i386), a working X display, and preferably OSS /dev/dsp (osspd)
# for FMOD 3.75 audio. Headless Xvfb currently dies with a null deref after
# title.map load on this binary — use a real session for play comparison.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${REF_GAME_DIR:-$ROOT/ref/ll-1.1-linux}"

if [[ ! -x "$DEST/ll-linux-full" || ! -f "$DEST/libfmod.so" ]]; then
  echo "Reference game not ready. Run: tools/ref_game/fetch.sh" >&2
  exit 1
fi

cd "$DEST"
export LD_LIBRARY_PATH="$DEST:${LD_LIBRARY_PATH:-}"

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is unset. Start under a desktop session (or Xephyr), not bare SSH." >&2
  exit 1
fi

if [[ ! -e /dev/dsp ]]; then
  echo "warning: /dev/dsp missing — FMOD 3.75 expects OSS (try osspd)." >&2
fi

exec ./ll-linux-full "$@"
