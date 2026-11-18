// Конечный автомат жеста "Cmd+Shift, нажали и отпустили без других клавиш".
// Чистая структура без зависимостей от AppKit — легко тестируется.

struct GestureMachine {
    enum Event {
        case flags(cmd: Bool, shift: Bool, ctrl: Bool, alt: Bool)
        case keyDown
        case mouseDown
    }

    private var cmd = false
    private var shift = false
    private var armed = false
    private var cancelled = false

    /// Сброс после потери событий (tap был отключён). Если модификаторы сейчас зажаты,
    /// пропущенные нажатия могли быть частью жеста — отменяем его до полного отпускания.
    mutating func reset(modifiersHeld: Bool) {
        self = GestureMachine()
        cancelled = modifiersHeld
    }

    /// Возвращает true, если нужно переключить раскладку.
    mutating func handle(_ event: Event) -> Bool {
        switch event {
        case .keyDown, .mouseDown:
            // Любая клавиша/клик при зажатом Cmd или Shift отменяет жест.
            if cmd || shift { cancelled = true }
            return false

        case let .flags(c, s, ctrl, alt):
            cmd = c
            shift = s
            if ctrl || alt { cancelled = true }
            if c && s && !cancelled { armed = true }
            if !c && !s {
                // Оба отпущены: жест завершён.
                let fire = armed && !cancelled
                armed = false
                cancelled = ctrl || alt
                return fire
            }
            return false
        }
    }
}

/// Самотест: `LangSwitcher --self-test`. Возвращает число провалов.
func runSelfTest() -> Int32 {
    typealias E = GestureMachine.Event
    func f(_ c: Bool = false, _ s: Bool = false, _ ctrl: Bool = false, _ a: Bool = false) -> E {
        .flags(cmd: c, shift: s, ctrl: ctrl, alt: a)
    }
    let cases: [(String, [E], Int)] = [
        ("Cmd↓ Shift↓ Shift↑ Cmd↑", [f(true), f(true, true), f(true), f()], 1),
        ("Shift↓ Cmd↓ Cmd↑ Shift↑", [f(false, true), f(true, true), f(false, true), f()], 1),
        ("Cmd↓ Shift↓ Z↓ Z↑ Shift↑ Cmd↑", [f(true), f(true, true), .keyDown, f(true), f()], 0),
        ("Cmd↓ Z↓ Shift↓ Shift↑ Cmd↑ (клавиша до Shift)", [f(true), .keyDown, f(true, true), f(true), f()], 0),
        ("Cmd+Shift затем Ctrl", [f(true), f(true, true), f(true, true, true), f(true, true), f()], 0),
        ("Cmd+Shift затем Option", [f(true), f(true, true), f(true, true, false, true), f()], 0),
        ("Ctrl↓ затем Cmd↓ Shift↓", [f(false, false, true), f(true, false, true), f(true, true, true), f(false, false, true), f()], 0),
        ("Cmd↓ Shift↓ клик мыши", [f(true), f(true, true), .mouseDown, f(true), f()], 0),
        ("Только Cmd", [f(true), f()], 0),
        ("Только Shift", [f(false, true), f()], 0),
        ("Cmd↓ Shift↓ Shift↑ Shift↓ Cmd↑ Shift↑ (один раз)", [f(true), f(true, true), f(true), f(true, true), f(false, true), f()], 1),
        ("Два жеста подряд", [f(true), f(true, true), f(), f(true), f(true, true), f()], 2),
        ("После отмены новый жест работает", [f(true), f(true, true), .keyDown, f(), f(true, true), f()], 1),
        ("Клавиша без модификаторов не влияет", [.keyDown, f(true, true), f()], 1),
    ]
    var failures: Int32 = 0
    for (name, events, expected) in cases {
        var m = GestureMachine()
        var fired = 0
        for e in events where m.handle(e) { fired += 1 }
        let ok = fired == expected
        if !ok { failures += 1 }
        print("\(ok ? "PASS" : "FAIL")  \(name): сработало \(fired), ожидалось \(expected)")
    }
    print(failures == 0 ? "Все тесты пройдены" : "Провалено: \(failures)")
    return failures
}
