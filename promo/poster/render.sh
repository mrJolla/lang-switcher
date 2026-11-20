#!/bin/sh
# Render poster.png (1080x1920) from poster.template.html with headless Chrome.
set -e
cd "$(dirname "$0")"
ICON=$(base64 -i ../../Resources/icon/AppIcon-1024.png)
sed "s|@ICON@|$ICON|" poster.template.html > /tmp/langswitcher-poster.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --window-size=1080,1920 --screenshot="$PWD/poster.png" file:///tmp/langswitcher-poster.html 2>/dev/null
rm /tmp/langswitcher-poster.html
