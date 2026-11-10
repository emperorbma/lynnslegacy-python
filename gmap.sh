#!/bin/sh
# Launch the FreeBASIC map editor (gmap). Binary must sit next to data/.
cd "$(dirname "$0")" || exit 1

if [ ! -f ./gmap.exe ]; then
    echo "gmap.exe not found in the project root."
    echo "Build it with: ./build_gmap.sh"
    if [ -t 0 ]; then
        printf "Press Enter to continue..."
        read -r _
    fi
    exit 1
fi

# Native Windows PE under Wine, or a FreeBASIC Linux build still named gmap.exe.
if command -v wine >/dev/null 2>&1 && file -b ./gmap.exe 2>/dev/null | grep -qi 'PE32'; then
    exec wine ./gmap.exe "$@"
fi

if [ -x ./gmap.exe ]; then
    exec ./gmap.exe "$@"
fi

# Non-executable PE without wine detection above: try wine anyway.
if command -v wine >/dev/null 2>&1; then
    exec wine ./gmap.exe "$@"
fi

echo "Cannot run gmap.exe (not executable, and wine not found)."
if [ -t 0 ]; then
    printf "Press Enter to continue..."
    read -r _
fi
exit 1
