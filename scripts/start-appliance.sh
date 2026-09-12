#!/bin/bash

FORDO_URL="http://127.0.0.1:8080"
HEALTH_URL="$FORDO_URL/api/health"

# Wait until the Fordo service is available.
until curl -fsS "$HEALTH_URL" >/dev/null 2>&1; do
    sleep 2
done

# Give NDI discovery a moment to initialize.
sleep 3

BROWSER=""

for candidate in chromium chromium-browser google-chrome google-chrome-stable; do
    if command -v "$candidate" >/dev/null 2>&1; then
        BROWSER="$(command -v "$candidate")"
        break
    fi
done

if [ -z "$BROWSER" ]; then
    echo "Fordo appliance startup failed: no supported Chromium-based browser found." >&2
    exit 1
fi

exec "$BROWSER" \
    --user-data-dir="$HOME/.config/fordo-chromium" \
    --password-store=basic \
    --kiosk \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --disable-translate \
    --autoplay-policy=no-user-gesture-required \
    "$FORDO_URL/?appliance=1"
