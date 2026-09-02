#!/bin/sh
cd "$(dirname "$0")" || exit 1

if [ ! -x ".venv/bin/python" ]; then
    echo "Virtual environment not found."
    echo "Create it with:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/python -m pip install -e \".[dev]\""
    if [ -t 0 ]; then
        printf "Press Enter to continue..."
        read -r _
    fi
    exit 1
fi

case "$1" in
    -h|--help|help|"/?")
        echo "Usage: run.sh [objects|map|palette|audio|config|test|help] [map] [--save spec]"
        echo "  objects [map]  walk Lynn (default: splash + title.map)"
        echo "  map [map]      tiles only (default: forest_fall)"
        echo "  palette        256-color ramp + lynn24.spr"
        echo "  config         key setup (data/controls.xml + ll.ini)"
        echo "  audio          live sound check (title.it); Esc quits"
        echo "  test           pytest (silent audio; e.g. run.sh test --map valley)"
        echo "  --save spec    load a save (path, N for ll_saveN.sav, or example name)"
        exit 0
        ;;
esac

.venv/bin/python -m lynn "$@"
status=$?
if [ "$status" -ne 0 ] && [ -t 0 ]; then
    printf "Press Enter to continue..."
    read -r _
fi
exit "$status"
