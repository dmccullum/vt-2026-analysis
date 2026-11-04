#!/bin/sh
# Render docs/share/card.html to docs/share/og.png (1200x630) with headless Chrome.
set -e
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
python3 -m http.server 8650 --directory docs >/dev/null 2>&1 &
PID=$!
trap 'kill $PID' EXIT
sleep 1
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1200,630 --virtual-time-budget=5000 \
  --screenshot="$PWD/docs/share/og.png" "http://localhost:8650/share/card.html" >/dev/null 2>&1
echo "wrote docs/share/og.png"
