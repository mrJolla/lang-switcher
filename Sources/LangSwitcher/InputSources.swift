import Carbon
import os

private let swlog = Logger(subsystem: "io.github.mrjolla.langswitcher", category: "switch")

/// Работа с источниками ввода (TIS).
enum InputSources {
    static func prop(_ s: TISInputSource, _ key: CFString) -> AnyObject? {
        guard let p = TISGetInputSourceProperty(s, key) else { return nil }
        return Unmanaged<AnyObject>.fromOpaque(p).takeUnretainedValue()
    }

    static func id(_ s: TISInputSource) -> String {
        prop(s, kTISPropertyInputSourceID) as? String ?? ""
    }

    /// Все включённые, выбираемые клавиатурные источники в системном порядке.
    /// Нюанс: TISCreateInputSourceList(includeAllInstalled: false) на этой системе не отдаёт
    /// включённые режимы CJK-методов (напр. Korean.2SetKorean), поэтому берём полный список
    /// и фильтруем по IsEnabled сами; порядок — как в com.apple.HIToolbox AppleEnabledInputSources.
    static func enabledList() -> [TISInputSource] {
        let filter: [CFString: Any] = [
            kTISPropertyInputSourceCategory: kTISCategoryKeyboardInputSource as Any,
            kTISPropertyInputSourceIsSelectCapable: true,
        ]
        guard let all = TISCreateInputSourceList(filter as CFDictionary, true)?
            .takeRetainedValue() as? [TISInputSource] else { return [] }
        let enabled = all.filter { prop($0, kTISPropertyInputSourceIsEnabled) as? Bool == true }

        // Системный порядок из настроек.
        let prefs = CFPreferencesCopyAppValue("AppleEnabledInputSources" as CFString,
                                              "com.apple.HIToolbox" as CFString) as? [[String: Any]] ?? []
        let order: [String] = prefs.compactMap {
            if let m = $0["Input Mode"] as? String { return m }
            if let n = $0["KeyboardLayout Name"] as? String { return "com.apple.keylayout." + n }
            return $0["Bundle ID"] as? String
        }
        func rank(_ s: TISInputSource) -> Int { order.firstIndex(of: id(s)) ?? Int.max }
        // sorted(by:) нестабилен по контракту — добавляем исходный индекс.
        // Часть режимов (Ainu, Japanese) отдаёт IsEnabled=true без реального включения —
        // при наличии настроек оставляем только те, что в них перечислены.
        let known = order.isEmpty ? enabled : enabled.filter { order.contains(id($0)) }
        return known.enumerated()
            .sorted { (rank($0.element), $0.offset) < (rank($1.element), $1.offset) }
            .map(\.element)
    }

    // MARK: выбор раскладок для цикла

    private static let disabledKey = "disabledLayouts"      // снятые пользователем галочки
    private static let unselectableKey = "unselectableLayouts"  // TISSelectInputSource вернул ошибку
    private static let probedKey = "probedLayouts"

    private static func set(_ key: String) -> Set<String> {
        Set(UserDefaults.standard.stringArray(forKey: key) ?? [])
    }
    private static func store(_ s: Set<String>, _ key: String) {
        UserDefaults.standard.set(s.sorted(), forKey: key)
    }

    static func isUserEnabled(_ s: TISInputSource) -> Bool { !set(disabledKey).contains(id(s)) }
    static func isUnselectable(_ s: TISInputSource) -> Bool { set(unselectableKey).contains(id(s)) }

    static func setUserEnabled(_ on: Bool, id sid: String) {
        var d = set(disabledKey)
        if on { d.remove(sid) } else { d.insert(sid) }
        store(d, disabledKey)
    }

    static func markUnselectable(_ sid: String) {
        var u = set(unselectableKey); u.insert(sid); store(u, unselectableKey)
        swlog.error("layout \(sid, privacy: .public) is not selectable, excluded from cycle")
    }

    static func localizedName(_ s: TISInputSource) -> String {
        prop(s, kTISPropertyLocalizedName) as? String ?? id(s)
    }

    /// Один раз пробуем выбрать режимы ввода (CJK и т.п.), которые могут не выбираться
    /// (rc -50 у Korean), и исключаем те, что не выбираются. Обычные раскладки не пробуем.
    /// Текущая раскладка восстанавливается.
    static func probeSelectability() {
        let original = current()
        var probed = set(probedKey)
        var switched = false
        for s in enabledList() {
            let sid = id(s)
            let type = prop(s, kTISPropertyInputSourceType) as? String ?? ""
            guard type != (kTISTypeKeyboardLayout as String), !probed.contains(sid) else { continue }
            probed.insert(sid)
            let rc = TISSelectInputSource(s)
            swlog.notice("probe \(sid, privacy: .public) rc=\(rc)")
            switched = true
            if rc != 0 { markUnselectable(sid) }
        }
        store(probed, probedKey)
        if switched, let original { TISSelectInputSource(original) }
    }

    /// Раскладки, участвующие в цикле.
    static func cycleList() -> [TISInputSource] {
        enabledList().filter { isUserEnabled($0) && !isUnselectable($0) }
    }

    static func current() -> TISInputSource? {
        TISCopyCurrentKeyboardInputSource()?.takeRetainedValue()
    }

    /// Короткая метка: первые 2 буквы первого языка.
    static func label(_ s: TISInputSource?) -> String {
        guard let s, let langs = prop(s, kTISPropertyInputSourceLanguages) as? [String],
              let first = langs.first else { return "??" }
        return String(first.prefix(2)).uppercased()
    }

    private static var switchGeneration = 0

    static func switchToNext() {
        switchGeneration += 1
        let gen = switchGeneration
        let list = cycleList()
        guard list.count > 1 else {
            log.error("switch: cycle list has \(list.count) sources, nothing to do")
            return
        }
        let curID = current().map(id) ?? ""
        let idx = list.firstIndex { id($0) == curID } ?? -1
        // Если источник не выбирается (rc != 0, напр. -50 у Korean при недоступном IME),
        // пропускаем его и пробуем следующий, иначе цикл застрянет на предыдущем.
        var next = list[(idx + 1) % list.count]
        var nextID = id(next)
        for step in 1...list.count {
            next = list[(idx + step) % list.count]
            nextID = id(next)
            if nextID == curID { return }
            let rc = TISSelectInputSource(next)
            swlog.notice("switch: \(curID, privacy: .public) -> \(nextID, privacy: .public) rc=\(rc) now=\(current().map(id) ?? "?", privacy: .public)")
            if rc == 0 { break }
            markUnselectable(nextID)
        }
        // Обход бага macOS: выбор CJK-метода иногда не применяется — проверяем и повторяем.
        for delay in [0.08, 0.25] {
            DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
                // Новое переключение отменяет отложенные повторы старого.
                if gen == switchGeneration, current().map(id) != nextID {
                    let rc = TISSelectInputSource(next)
                    log.notice("switch retry after \(delay)s rc=\(rc) target=\(nextID, privacy: .public)")
                }
            }
        }
    }

    static func printList() {
        func dump(_ title: String, _ list: [TISInputSource]) {
            print(title)
            for s in list {
                let cat = (prop(s, kTISPropertyInputSourceCategory) as? String ?? "?")
                    .replacingOccurrences(of: "TISCategory", with: "")
                let type = (prop(s, kTISPropertyInputSourceType) as? String ?? "?")
                    .replacingOccurrences(of: "TISType", with: "")
                let sel = prop(s, kTISPropertyInputSourceIsSelectCapable) as? Bool ?? false
                print("  \(id(s)) | category=\(cat) | type=\(type) | selectable=\(sel) | label=\(label(s))")
            }
        }
        let all = TISCreateInputSourceList(nil, false)?.takeRetainedValue() as? [TISInputSource] ?? []
        dump("Все включённые источники:", all)
        dump("Все включённые (для меню):", enabledList())
        dump("Цикл переключения:", cycleList())
        print("Текущий: \(current().map(id) ?? "?")")
    }
}
