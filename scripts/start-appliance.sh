#!/bin/bash

FORDO_URL="http://127.0.0.1:8080"
HEALTH_URL="$FORDO_URL/api/health"

# Wait until the Fordo service is available.
until curl -fsS "$HEALTH_URL" >/dev/null 2>&1; do
    sleep 2
done

# Give NDI discovery a moment to initialize.
sleep 3

exec /usr/bin/chromium \
    --user-data-dir=/home/metrotimer/.config/fordo-chromium \
    --password-store=basic \
    --kiosk \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --disable-translate \
    --autoplay-policy=no-user-gesture-required \
    "$FORDO_URL/?appliance=1"
