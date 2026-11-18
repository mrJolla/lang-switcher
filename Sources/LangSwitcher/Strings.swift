import Foundation

/// Все видимые пользователю строки меню. Ключи живут в Resources/<lang>.lproj/Localizable.strings;
/// проверка паритета ключей — `make test` (scripts/check_strings.py).
enum L10n {
    static var enabled: String { NSLocalizedString("menu.enabled", value: "Enabled", comment: "Menu: toggle switching on/off") }
    static var launchAtLogin: String { NSLocalizedString("menu.launchAtLogin", value: "Launch at Login", comment: "Menu: start the app at login") }
    static var layouts: String { NSLocalizedString("menu.layouts", value: "Layouts", comment: "Menu: submenu with keyboard layouts") }
    static func layoutUnavailable(_ name: String) -> String {
        String(format: NSLocalizedString("menu.layoutUnavailable", value: "%@ (unavailable)", comment: "Menu: layout that cannot be selected; %@ is the layout name"), name)
    }
    static var permissionGranted: String { NSLocalizedString("menu.permissionGranted", value: "Permission granted", comment: "Menu status: Input Monitoring granted") }
    static var permissionNeeded: String { NSLocalizedString("menu.permissionNeeded", value: "Input Monitoring permission needed", comment: "Menu status: Input Monitoring missing") }
    static var grantPermission: String { NSLocalizedString("menu.grantPermission", value: "Grant Permission…", comment: "Menu: opens Privacy settings") }
    static var quit: String { NSLocalizedString("menu.quit", value: "Quit", comment: "Menu: quit the app") }

    /// Отладка: `LangSwitcher -AppleLanguages '(de)' --print-menu`.
    static func printMenu() {
        print("localization: \(Bundle.main.preferredLocalizations.first ?? "?")")
        print("menu.enabled=\(enabled)")
        print("menu.launchAtLogin=\(launchAtLogin)")
        print("menu.layouts=\(layouts)")
        print("menu.layoutUnavailable=\(layoutUnavailable("ABC"))")
        print("menu.permissionGranted=\(permissionGranted)")
        print("menu.permissionNeeded=\(permissionNeeded)")
        print("menu.grantPermission=\(grantPermission)")
        print("menu.quit=\(quit)")
    }
}
