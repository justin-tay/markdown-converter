#!/usr/bin/env bash
# Markdown Converter for macOS and Linux.
#   ./convert.sh <file-or-folder> [options]    (see --help)
#   ./convert.sh                                (asks for a file or folder)
# The first run sets up a private Python environment in .venv (Setup); later
# runs reuse it. Conversion itself never uses the internet.
# convert.command wraps this script for double-clicking in the macOS Finder.
set -u

here="$(cd "$(dirname "$0")" && pwd)"
venv="$here/.venv"
venv_py="$venv/bin/python"
stamp="$venv/requirements.lock.installed"
lock="$here/requirements.lock"
newest_python=14
supported_pythons="3.12, 3.13 or 3.14"
case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) bundle="$here/offline-bundle/macos-arm64" ;;
    Darwin-*)
        # Intel Macs: onnxruntime has no Intel builds for Python 3.14 (see that lock file).
        bundle="$here/offline-bundle/macos-x64"
        lock="$here/requirements-macos-x64.lock"
        newest_python=13
        supported_pythons="3.12 or 3.13"
        ;;
    *) bundle="$here/offline-bundle/linux-$(uname -m)" ;;
esac

find_python() {
    for candidate in python3 python python3.14 python3.13 python3.12; do
        if command -v "$candidate" >/dev/null 2>&1 &&
            "$candidate" -c "import sys; sys.exit(0 if (3, 12) <= sys.version_info[:2] <= (3, $newest_python) else 1)" 2>/dev/null; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

setup_failed() {
    echo >&2
    echo "Setup did not complete. Check the messages above. Without internet access," >&2
    echo "copy an Offline Bundle to \"$bundle\" first (see README)." >&2
    rm -f "$stamp"
    exit 1
}

if [ ! -x "$venv_py" ] || ! cmp -s "$lock" "$stamp"; then
    if ! python="$(find_python)"; then
        echo >&2
        echo "Python $supported_pythons is needed but was not found." >&2
        echo "Install it from https://www.python.org/downloads/ (or on a Mac with Homebrew:" >&2
        echo "brew install python@3.13), then run the Markdown Converter again." >&2
        exit 1
    fi
    echo "Setting up the Markdown Converter (first run only, this can take a few minutes)..."
    [ -x "$venv_py" ] || "$python" -m venv "$venv" || setup_failed
    if [ -d "$bundle" ]; then
        echo "Installing from the Offline Bundle in \"$bundle\"."
        "$venv_py" -m pip install --disable-pip-version-check --quiet --no-index \
            --find-links "$bundle" -r "$lock" || setup_failed
    else
        "$venv_py" -m pip install --disable-pip-version-check --quiet -r "$lock" || setup_failed
    fi
    cp "$lock" "$stamp"
    echo "Setup complete."
    echo
fi

PYTHONPATH="$here/src" exec "$venv_py" -m markdown_converter "$@"
