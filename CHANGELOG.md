# Changelog

## 1.1.0

- The menu now follows the system language: English, Russian, German, Spanish, Italian, French and Brazilian Portuguese (falls back to English).
- Website: Portuguese is now Brazilian Portuguese (pt-BR) with a Brazil flag; install-step texts match the app's menu labels.
- New debug flag `--print-menu` prints the localized menu titles and exits.
- `make test` now also checks that all `Localizable.strings` files have the same keys and pass `plutil -lint`.
- After updating, Input Monitoring may need to be re-enabled (the ad-hoc signature changes with every build). If switching stops working, run `tccutil reset ListenEvent io.github.mrjolla.langswitcher`, then grant the permission again from the menu.

## 1.0.0

- First release: switch the keyboard layout with a Cmd+Shift tap, cycle through enabled layouts, choose which layouts take part, current layout label in the menu bar, launch at login.
- Universal binary (Apple Silicon and Intel), macOS 13+, ad-hoc signed (not notarized).
