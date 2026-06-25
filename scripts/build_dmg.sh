#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Qwen Desktop"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="dist/${APP_NAME}.dmg"
STAGING="dist/dmg_staging"
VOLUME_NAME="Qwen Desktop"

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "ERROR: ${APP_BUNDLE} not found. Run 'make build' first."
    exit 1
fi

# Create staging directory
rm -rf "${STAGING}"
mkdir -p "${STAGING}"

# Copy app bundle
cp -R "${APP_BUNDLE}" "${STAGING}/"

# Create symbolic link to /Applications
ln -s /Applications "${STAGING}/Applications"

# Create DMG
rm -f "${DMG_NAME}"

# Calculate approximate size (app size + 50MB margin)
APP_SIZE=$(du -sm "${APP_BUNDLE}" | cut -f1)
DMG_SIZE=$((APP_SIZE + 50))

hdiutil create \
    -volname "${VOLUME_NAME}" \
    -srcfolder "${STAGING}" \
    -size "${DMG_SIZE}m" \
    -format UDZO \
    -imagekey zlib-level=9 \
    "${DMG_NAME}"

# Clean up
rm -rf "${STAGING}"

echo "✅ DMG created: ${DMG_NAME}"
