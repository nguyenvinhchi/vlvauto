#!/bin/bash

# Build settings
PATH_SEPARATOR=":"
# SCRIPT="auto_qt_main.py"
SCRIPT="autov2_main.py"
DIST_FOLDER="dist"
BUILD_FOLDER="build"
SPEC_FILE="${SCRIPT%.py}.spec"

# Clean old builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_FOLDER" "$DIST_FOLDER" "$SPEC_FILE"

# Run PyInstaller
echo "🚀 Building executable with PyInstaller..."
pyinstaller --noconfirm --onefile --windowed "$SCRIPT" \
  --name game_tool \
  --icon game_icon_129066.ico \
  --add-data "data${PATH_SEPARATOR}data"

# Done
echo "✅ Build complete. Executable located in $DIST_FOLDER/"
