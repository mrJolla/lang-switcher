import AppKit
import Carbon
import ServiceManagement
import os

let log = Logger(subsystem: "io.github.mrjolla.langswitcher", category: "main")

if CommandLine.arguments.contains("--list-sources") { InputSources.printList(); exit(0) }
if CommandLine.arguments.contains("--preflight") { exit(CGPreflightListenEventAccess() ? 0 : 1) }
if CommandLine.arguments.contains("--switch-next") {
    let before = InputSources.current().map(InputSources.id) ?? "?"
    InputSources.switchToNext()
    // Повторы переключения идут через main queue — крутим run loop, затем печатаем итог.
    RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.6))
    print("before=\(before) after=\(InputSources.current().map(InputSources.id) ?? "?")")
    exit(0)
}
if CommandLine.arguments.contains("--print-menu") { L10n.printMenu(); exit(0) }
if CommandLine.arguments.contains("--self-test") { exit(runSelfTest()) }

let enabledKey = "enabled"

final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    var machine = GestureMachine()
    var tap: CFMachPort?
    var pollTimer: Timer?
    var pollCount = 0
    var tapSource: CFRunLoopSource?
    var tapTrusted = false

    var isEnabled: Bool {
        get { UserDefaults.standard.object(forKey: enabledKey) as? Bool ?? true }
        set { UserDefaults.standard.set(newValue, forKey: enabledKey) }
    }

    func applicationDidFinishLaunching(_ n: Notification) {
        let menu = NSMenu()
        menu.delegate = self
        statusItem.menu = menu
        updateTitle()
        DistributedNotificationCenter.default().addObserver(
            forName: NSNotification.Name(kTISNotifySelectedKeyboardInputSourceChanged as String),
            object: nil, queue: .main) { [weak self] _ in self?.updateTitle() }
        log.notice("launch pid=\(getpid()) enabled=\(self.isEnabled) preflight=\(CGPreflightListenEventAccess())")
        DispatchQueue.main.async { InputSources.probeSelectability(); self.updateTitle() }
        setupTap()
        if tap == nil || !tapTrusted {
            if !CGPreflightListenEventAccess() { _ = CGRequestListenEventAccess() }
            pollTimer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in
                self?.setupTap()
            }
        }
    }

    func updateTitle() {
        statusItem.button?.title = InputSources.label(InputSources.current())
    }

    // MARK: event tap

    func setupTap() {
        // tapCreate может вернуть не-nil даже без разрешения (tap без клавиатурных событий,
        // события приходят частично — не признак доступа), поэтому доверяем только preflight.
        // Preflight может отстать от выдачи разрешения — после его перехода в true
        // пересоздаём tap.
        pollCount += 1
        let pre = CGPreflightListenEventAccess()
        if !pre { relaunchIfGrantedInFreshProcess() }
        if tap != nil {
            if pre && !tapTrusted {
                log.notice("permission now granted, recreating tap")
                teardownTap()
            } else { return }
        }
        let types: [CGEventType] = [.flagsChanged, .keyDown, .leftMouseDown, .rightMouseDown, .otherMouseDown]
        let mask = types.reduce(CGEventMask(0)) { $0 | (1 << $1.rawValue) }
        let callback: CGEventTapCallBack = { _, type, event, refcon in
            let me = Unmanaged<AppDelegate>.fromOpaque(refcon!).takeUnretainedValue()
            me.handle(type: type, event: event)
            return Unmanaged.passUnretained(event)
        }
        guard let port = CGEvent.tapCreate(
            tap: .cgSessionEventTap, place: .tailAppendEventTap, options: .listenOnly,
            eventsOfInterest: mask, callback: callback,
            userInfo: Unmanaged.passUnretained(self).toOpaque()) else {
            if pollCount == 1 || pollCount % 15 == 0 {
                log.notice("tapCreate failed (poll #\(self.pollCount)) preflight=\(pre)")
            }
            return
        }
        log.notice("tap created (poll #\(self.pollCount)) preflight=\(pre)")
        tap = port
        tapTrusted = pre
        let src = CFMachPortCreateRunLoopSource(nil, port, 0)
        tapSource = src
        CFRunLoopAddSource(CFRunLoopGetMain(), src, .commonModes)
        CGEvent.tapEnable(tap: port, enable: true)
        if pre { pollTimer?.invalidate(); pollTimer = nil }
    }

    /// Preflight кэшируется в процессе. Свежий процесс (`--preflight`) отвечает правдиво —
    /// если он говорит «выдано», перезапускаем себя.
    func relaunchIfGrantedInFreshProcess() {
        guard let exe = Bundle.main.executablePath else { return }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: exe)
        p.arguments = ["--preflight"]
        guard (try? p.run()) != nil else { return }
        p.waitUntilExit()
        guard p.terminationStatus == 0 else { return }
        log.notice("fresh process reports permission granted, relaunching")
        let r = Process()
        r.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        r.arguments = ["-n", Bundle.main.bundlePath]
        try? r.run()
        NSApp.terminate(nil)
    }

    func teardownTap() {
        if let tap { CGEvent.tapEnable(tap: tap, enable: false); CFMachPortInvalidate(tap) }
        if let tapSource { CFRunLoopRemoveSource(CFRunLoopGetMain(), tapSource, .commonModes) }
        tap = nil; tapSource = nil; tapTrusted = false
        machine = GestureMachine()
    }

    // Вызывается на главном потоке (источник добавлен в main run loop).
    func handle(type: CGEventType, event: CGEvent) {
        let result: Bool
        switch type {
        case .tapDisabledByTimeout, .tapDisabledByUserInput:
            if let tap { CGEvent.tapEnable(tap: tap, enable: true) }
            let held = CGEventSource.flagsState(.combinedSessionState)
                .intersection([.maskCommand, .maskShift, .maskControl, .maskAlternate])
            machine.reset(modifiersHeld: !held.isEmpty)
            return
        case .flagsChanged:
            let f = event.flags
            log.debug("flagsChanged raw=\(f.rawValue, format: .hex)")
            result = machine.handle(.flags(cmd: f.contains(.maskCommand), shift: f.contains(.maskShift),
                                           ctrl: f.contains(.maskControl), alt: f.contains(.maskAlternate)))
        case .keyDown:
            result = machine.handle(.keyDown)
        default:
            result = machine.handle(.mouseDown)
        }
        if result {
            log.notice("gesture fired, enabled=\(self.isEnabled)")
            if isEnabled { InputSources.switchToNext() }
        }
    }

    // MARK: menu

    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()
        let en = NSMenuItem(title: L10n.enabled, action: #selector(toggleEnabled), keyEquivalent: "")
        en.target = self; en.state = isEnabled ? .on : .off
        menu.addItem(en)

        let login = NSMenuItem(title: L10n.launchAtLogin, action: #selector(toggleLogin), keyEquivalent: "")
        login.target = self; login.state = SMAppService.mainApp.status == .enabled ? .on : .off
        menu.addItem(login)
        menu.addItem(.separator())

        let layouts = NSMenu()
        for s in InputSources.enabledList() {
            let sid = InputSources.id(s)
            let bad = InputSources.isUnselectable(s)
            let it = NSMenuItem(title: bad ? L10n.layoutUnavailable(InputSources.localizedName(s)) : InputSources.localizedName(s),
                                action: #selector(toggleLayout(_:)), keyEquivalent: "")
            it.target = self; it.representedObject = sid
            it.state = (!bad && InputSources.isUserEnabled(s)) ? .on : .off
            it.isEnabled = !bad
            layouts.addItem(it)
        }
        let layoutsItem = NSMenuItem(title: L10n.layouts, action: nil, keyEquivalent: "")
        layoutsItem.submenu = layouts
        menu.addItem(layoutsItem)

        let granted = tapTrusted || CGPreflightListenEventAccess()
        let status = NSMenuItem(title: granted ? L10n.permissionGranted : L10n.permissionNeeded,
                                action: nil, keyEquivalent: "")
        status.isEnabled = false
        menu.addItem(status)
        if !granted {
            let grant = NSMenuItem(title: L10n.grantPermission, action: #selector(openPrivacy), keyEquivalent: "")
            grant.target = self
            menu.addItem(grant)
        }
        menu.addItem(.separator())
        let quit = NSMenuItem(title: L10n.quit, action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        menu.addItem(quit)
    }

    @objc func toggleLayout(_ item: NSMenuItem) {
        guard let sid = item.representedObject as? String else { return }
        InputSources.setUserEnabled(item.state != .on, id: sid)
    }

    @objc func toggleEnabled() { isEnabled.toggle() }

    @objc func toggleLogin() {
        do {
            if SMAppService.mainApp.status == .enabled { try SMAppService.mainApp.unregister() }
            else { try SMAppService.mainApp.register() }
        } catch {
            NSLog("LangSwitcher: автозапуск: \(error)")
        }
    }

    @objc func openPrivacy() {
        _ = CGRequestListenEventAccess()
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent") {
            NSWorkspace.shared.open(url)
        }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
