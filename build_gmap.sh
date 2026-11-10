#!/bin/sh
# Build FreeBASIC gmap.exe and place it next to data/ (gmap ChDir ExePath).
cd "$(dirname "$0")" || exit 1

if ! command -v fbc >/dev/null 2>&1; then
    echo "FreeBASIC compiler (fbc) not found on PATH."
    echo "Install FreeBASIC, then re-run ./build_gmap.sh"
    if [ -t 0 ]; then
        printf "Press Enter to continue..."
        read -r _
    fi
    exit 1
fi

if ! command -v make >/dev/null 2>&1; then
    echo "GNU make not found on PATH."
    if [ -t 0 ]; then
        printf "Press Enter to continue..."
        read -r _
    fi
    exit 1
fi

mkdir -p fbsrc/src/gmap/obj
make -C fbsrc/src/gmap "$@" || {
    status=$?
    if [ -t 0 ]; then
        printf "Press Enter to continue..."
        read -r _
    fi
    exit "$status"
}

if [ ! -f fbsrc/gmap.exe ]; then
    echo "Build finished but fbsrc/gmap.exe is missing."
    if [ -t 0 ]; then
        printf "Press Enter to continue..."
        read -r _
    fi
    exit 1
fi

cp -f fbsrc/gmap.exe ./gmap.exe
echo "Built ./gmap.exe (run with ./gmap.sh or gmap.bat)."
