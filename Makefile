APP      = build/LangSwitcher.app
BIN      = $(APP)/Contents/MacOS/LangSwitcher
SOURCES  = $(wildcard Sources/LangSwitcher/*.swift)
DEST     = $(HOME)/Applications/LangSwitcher.app
DESTDIR_APPS = $(HOME)/Applications
ICNS     = Resources/AppIcon.icns
# Версия берётся из Info.plist (единственный источник).
VERSION  = $(shell /usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" Info.plist)
DMG      = dist/LangSwitcher-$(VERSION).dmg
SWIFTFLAGS = -O -swift-version 5

.PHONY: build release dmg install uninstall clean test

# Быстрая dev-сборка (только arm64).
build: $(SOURCES) Info.plist
	rm -rf $(APP)
	mkdir -p $(APP)/Contents/MacOS $(APP)/Contents/Resources
	swiftc $(SWIFTFLAGS) -target arm64-apple-macos13.0 $(SOURCES) -o $(BIN)
	cp Info.plist $(APP)/Contents/Info.plist
	@if [ -f $(ICNS) ]; then cp $(ICNS) $(APP)/Contents/Resources/AppIcon.icns; fi
	codesign --force --deep --sign - $(APP)
	@echo "Собрано: $(APP)"

# Универсальная сборка (arm64 + x86_64), ad-hoc подпись.
release: $(SOURCES) Info.plist
	rm -rf $(APP) build/LangSwitcher-arm64 build/LangSwitcher-x86_64
	mkdir -p $(APP)/Contents/MacOS $(APP)/Contents/Resources
	swiftc $(SWIFTFLAGS) -target arm64-apple-macos13.0 $(SOURCES) -o build/LangSwitcher-arm64
	swiftc $(SWIFTFLAGS) -target x86_64-apple-macos13.0 $(SOURCES) -o build/LangSwitcher-x86_64
	lipo -create build/LangSwitcher-arm64 build/LangSwitcher-x86_64 -output $(BIN)
	rm -f build/LangSwitcher-arm64 build/LangSwitcher-x86_64
	cp Info.plist $(APP)/Contents/Info.plist
	@if [ -f $(ICNS) ]; then cp $(ICNS) $(APP)/Contents/Resources/AppIcon.icns; fi
	codesign --force --sign - --timestamp=none $(APP)
	lipo -info $(BIN)
	codesign --verify --deep --strict --verbose=2 $(APP)
	@echo "Собрано (universal): $(APP)"

dmg: release
	rm -rf build/dmg dist
	mkdir -p build/dmg dist
	cp -R $(APP) build/dmg/
	ln -s /Applications build/dmg/Applications
	hdiutil create -volname "LangSwitcher" -srcfolder build/dmg -fs HFS+ -format UDZO -ov $(DMG)
	hdiutil verify $(DMG)
	rm -rf build/dmg
	@echo "Собрано: $(DMG)"

test: build
	$(BIN) --self-test

install: build
	-pkill -x LangSwitcher
	@sleep 0.5
	mkdir -p "$(DESTDIR_APPS)"
	rm -rf "$(DEST)"
	cp -R "$(APP)" "$(DEST)"
	open "$(DEST)"

uninstall:
	-pkill -x LangSwitcher
	rm -rf "$(DEST)"

clean:
	rm -rf build dist
