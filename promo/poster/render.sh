#!/bin/sh
# Render poster.png (RU) and poster.en.png (EN), 1080x1920, from poster.template.html with headless Chrome.
set -e
cd "$(dirname "$0")"
ICON=$(base64 -i ../../Resources/icon/AppIcon-1024.png)

render() { # $1=lang $2=output $3=title html $4=meta
  sed -e "s|@ICON@|$ICON|" -e "s|@LANG@|$1|" -e "s|@TITLE@|$3|" -e "s|@META@|$4|" poster.template.html > /tmp/langswitcher-poster.html
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1080,1920 --screenshot="$PWD/$2" file:///tmp/langswitcher-poster.html 2>/dev/null
  rm /tmp/langswitcher-poster.html
}

render ru poster.png 'Удобная<br>смена языка<br><span>на клавиатуре</span>' 'macOS 13+ · Apple Silicon и Intel'
render en poster.en.png 'Switch your<br>keyboard layout<br><span>with one tap</span>' 'macOS 13+ · Apple Silicon \&amp; Intel'
