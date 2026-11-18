// LangSwitcher icon generator (procedural, AppKit/CoreGraphics/CoreText).
// Usage:
//   swift Resources/icon/make_icon.swift <variant 1|2|3> <out.png>
//   swift Resources/icon/make_icon.swift all <out-dir>     // variant-1..3.png + variants-preview.png
// Variants: 1 = glassy keycap on blue; 2 = two overlapping tiles + swap badge on indigo;
//           3 = bold "A <-> Я" on graphite.
// Layout: 1024 canvas, ~824px continuous-corner squircle (100px margin), soft shadow, top highlight.
import AppKit

let S: CGFloat = 1024
let cs = CGColorSpace(name: CGColorSpace.sRGB)!
func C(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1) -> CGColor { CGColor(colorSpace: cs, components: [r/255, g/255, b/255, a])! }
func grad(_ cols: [CGColor], _ locs: [CGFloat]? = nil) -> CGGradient { CGGradient(colorsSpace: cs, colors: cols as CFArray, locations: locs)! }

func squircle(_ r: CGRect, _ n: CGFloat = 5) -> CGPath {
    let p = CGMutablePath(); let a = r.width/2, b = r.height/2, steps = 360
    for i in 0...steps {
        let t = CGFloat(i)/CGFloat(steps) * 2 * .pi
        let c = cos(t), s = sin(t)
        let x = r.midX + a * (c < 0 ? -1 : 1) * pow(abs(c), 2/n)
        let y = r.midY + b * (s < 0 ? -1 : 1) * pow(abs(s), 2/n)
        i == 0 ? p.move(to: CGPoint(x: x, y: y)) : p.addLine(to: CGPoint(x: x, y: y))
    }
    p.closeSubpath(); return p
}
func rrect(_ r: CGRect, _ rad: CGFloat) -> CGPath { CGPath(roundedRect: r, cornerWidth: rad, cornerHeight: rad, transform: nil) }

func vgrad(_ g: CGContext, _ path: CGPath, _ cols: [CGColor], _ locs: [CGFloat]? = nil) {
    g.saveGState(); g.addPath(path); g.clip()
    let b = path.boundingBox
    g.drawLinearGradient(grad(cols, locs), start: CGPoint(x: b.midX, y: b.maxY), end: CGPoint(x: b.midX, y: b.minY), options: [])
    g.restoreGState()
}
func shadowed(_ g: CGContext, dy: CGFloat, blur: CGFloat, alpha: CGFloat, _ draw: () -> Void) {
    g.saveGState(); g.setShadow(offset: CGSize(width: 0, height: -dy), blur: blur, color: C(0, 0, 0, alpha)); draw(); g.restoreGState()
}

func glyphPath(_ s: String, size: CGFloat, weight: NSFont.Weight, center: CGPoint, tracking: CGFloat = 0) -> CGPath {
    let font = NSFont.systemFont(ofSize: size, weight: weight)
    let chars = Array(s.utf16); var gl = [CGGlyph](repeating: 0, count: chars.count)
    CTFontGetGlyphsForCharacters(font, chars, &gl, chars.count)
    var adv = [CGSize](repeating: .zero, count: chars.count)
    CTFontGetAdvancesForGlyphs(font, .horizontal, gl, &adv, chars.count)
    let path = CGMutablePath(); var x: CGFloat = 0
    for i in 0..<chars.count {
        if let gp = CTFontCreatePathForGlyph(font, gl[i], nil) { path.addPath(gp, transform: CGAffineTransform(translationX: x, y: 0)) }
        x += adv[i].width + tracking
    }
    let bb = path.boundingBoxOfPath
    return path.copy(using: [CGAffineTransform(translationX: center.x - bb.midX, y: center.y - bb.midY)])!
}

func arrow(_ g: CGContext, from a: CGPoint, to b: CGPoint, width: CGFloat, head: CGFloat, color: CGColor) {
    let ang = atan2(b.y - a.y, b.x - a.x)
    g.saveGState(); g.setStrokeColor(color); g.setLineWidth(width); g.setLineCap(.round); g.setLineJoin(.round)
    g.move(to: a); g.addLine(to: b)
    for s in [-1.0, 1.0] { g.move(to: b); g.addLine(to: CGPoint(x: b.x - head*cos(ang + s*0.7), y: b.y - head*sin(ang + s*0.7))) }
    g.strokePath(); g.restoreGState()
}

// Base squircle with shadow, gradient, highlight, inner edge
func base(_ g: CGContext, _ cols: [CGColor], _ locs: [CGFloat]? = nil) -> CGPath {
    let r = CGRect(x: 100, y: 100, width: 824, height: 824), p = squircle(r)
    shadowed(g, dy: 12, blur: 28, alpha: 0.35) { g.addPath(p); g.setFillColor(cols[cols.count/2]); g.fillPath() }
    vgrad(g, p, cols, locs)
    // top gloss
    g.saveGState(); g.addPath(p); g.clip()
    g.drawLinearGradient(grad([C(255,255,255,0.28), C(255,255,255,0)]), start: CGPoint(x: 512, y: 924), end: CGPoint(x: 512, y: 560), options: [])
    g.restoreGState()
    // hairline inner stroke
    g.saveGState(); g.addPath(p); g.setStrokeColor(C(255,255,255,0.22)); g.setLineWidth(3); g.clip(); g.addPath(p); g.setLineWidth(6); g.strokePath(); g.restoreGState()
    return p
}

func variant1(_ g: CGContext) {
    _ = base(g, [C(94,170,255), C(40,105,240), C(52,52,200)])
    // keycap: base (side) + top face
    let w: CGFloat = 640, h: CGFloat = 560
    let side = CGRect(x: 512 - w/2, y: 512 - h/2 - 30, width: w, height: h)
    let face = CGRect(x: side.minX + 14, y: side.minY + 44, width: w - 28, height: h - 44)
    shadowed(g, dy: 22, blur: 40, alpha: 0.45) { g.addPath(rrect(side, 120)); g.setFillColor(C(150,160,190)); g.fillPath() }
    vgrad(g, rrect(side, 120), [C(214,222,240), C(150,162,196)])
    let fp = rrect(face, 104)
    vgrad(g, fp, [C(255,255,255), C(236,241,252)])
    // soft concave dish
    g.saveGState(); g.addPath(fp); g.clip()
    g.drawRadialGradient(grad([C(255,255,255,0), C(190,205,238,0.55)]), startCenter: CGPoint(x: face.midX, y: face.midY + 20), startRadius: 160, endCenter: CGPoint(x: face.midX, y: face.midY + 20), endRadius: 420, options: [])
    g.restoreGState()
    // diagonal split
    g.saveGState(); g.addPath(fp); g.clip()
    g.setStrokeColor(C(70,110,220,0.28)); g.setLineWidth(8); g.setLineCap(.round)
    g.move(to: CGPoint(x: face.midX + 70, y: face.maxY - 40)); g.addLine(to: CGPoint(x: face.midX - 70, y: face.minY + 40)); g.strokePath()
    g.restoreGState()
    let ink = [C(48,96,232), C(30,60,190)]
    let cy = face.midY + 6
    for (s, x, sz) in [("A", face.midX - 145, CGFloat(330)), ("Я", face.midX + 145, CGFloat(330))] {
        let gp = glyphPath(s, size: sz, weight: .heavy, center: CGPoint(x: x, y: cy))
        g.saveGState(); g.translateBy(x: 0, y: -4); g.addPath(gp); g.setFillColor(C(255,255,255,0.95)); g.fillPath(); g.restoreGState()
        vgrad(g, gp, ink)
    }
}

func tile(_ g: CGContext, _ r: CGRect, _ cols: [CGColor], _ s: String, ink: [CGColor], rot: CGFloat = 0) {
    g.saveGState()
    g.translateBy(x: r.midX, y: r.midY); g.rotate(by: rot); g.translateBy(x: -r.midX, y: -r.midY)
    let p = rrect(r, 110)
    shadowed(g, dy: 18, blur: 34, alpha: 0.4) { g.addPath(p); g.setFillColor(cols[0]); g.fillPath() }
    vgrad(g, p, cols)
    g.saveGState(); g.addPath(p); g.clip()
    g.drawLinearGradient(grad([C(255,255,255,0.35), C(255,255,255,0)]), start: CGPoint(x: r.midX, y: r.maxY), end: CGPoint(x: r.midX, y: r.midY + 40), options: [])
    g.restoreGState()
    let gp = glyphPath(s, size: 320, weight: .heavy, center: CGPoint(x: r.midX, y: r.midY))
    shadowed(g, dy: 6, blur: 10, alpha: 0.25) { g.addPath(gp); g.setFillColor(ink[0]); g.fillPath() }
    vgrad(g, gp, ink)
    g.restoreGState()
}
func variant2(_ g: CGContext) {
    _ = base(g, [C(150,120,255), C(96,70,225), C(60,40,170)])
    tile(g, CGRect(x: 200, y: 478, width: 410, height: 360), [C(255,255,255), C(226,230,248)], "A", ink: [C(110,84,240), C(70,50,200)])
    tile(g, CGRect(x: 414, y: 186, width: 410, height: 360), [C(255,168,92), C(255,92,90)], "Я", ink: [C(255,255,255), C(255,236,228)])
    // swap badge
    let c = CGPoint(x: 512, y: 512)
    shadowed(g, dy: 8, blur: 16, alpha: 0.4) { g.fillEllipse(in: CGRect(x: c.x-84, y: c.y-84, width: 168, height: 168)); }
    g.setFillColor(C(255,255,255)); g.fillEllipse(in: CGRect(x: c.x-84, y: c.y-84, width: 168, height: 168))
    let col = C(70,50,200)
    arrow(g, from: CGPoint(x: c.x-44, y: c.y+24), to: CGPoint(x: c.x+44, y: c.y+24), width: 18, head: 30, color: col)
    arrow(g, from: CGPoint(x: c.x+44, y: c.y-24), to: CGPoint(x: c.x-44, y: c.y-24), width: 18, head: 30, color: col)
}

func variant3(_ g: CGContext) {
    _ = base(g, [C(86,90,102), C(44,46,54), C(24,25,30)])
    let cy: CGFloat = 512
    for (s, x) in [("A", CGFloat(298)), ("Я", CGFloat(726))] {
        let gp = glyphPath(s, size: 330, weight: .bold, center: CGPoint(x: x, y: cy))
        shadowed(g, dy: 8, blur: 14, alpha: 0.5) { g.addPath(gp); g.setFillColor(C(255,255,255)); g.fillPath() }
        vgrad(g, gp, [C(255,255,255), C(206,210,222)])
    }
    let blue = [C(90,180,255), C(10,120,255)]
    // arrows drawn with gradient via clip of stroked path
    g.saveGState()
    let p = CGMutablePath()
    func addArrow(_ a: CGPoint, _ b: CGPoint) {
        let ang = atan2(b.y-a.y, b.x-a.x); p.move(to: a); p.addLine(to: b)
        for s in [-1.0, 1.0] { p.move(to: b); p.addLine(to: CGPoint(x: b.x - 42*cos(ang+s*0.7), y: b.y - 42*sin(ang+s*0.7))) }
    }
    addArrow(CGPoint(x: 450, y: 570), CGPoint(x: 574, y: 570))
    addArrow(CGPoint(x: 574, y: 454), CGPoint(x: 450, y: 454))
    let stroked = p.copy(strokingWithWidth: 26, lineCap: .round, lineJoin: .round, miterLimit: 10)
    shadowed(g, dy: 6, blur: 12, alpha: 0.5) { g.addPath(stroked); g.setFillColor(blue[1]); g.fillPath() }
    g.restoreGState()
    g.saveGState(); g.addPath(stroked); g.clip()
    g.drawLinearGradient(grad(blue), start: CGPoint(x: 512, y: 600), end: CGPoint(x: 512, y: 430), options: [])
    g.restoreGState()
}

func render(_ v: Int) -> NSBitmapImageRep {
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 1024, pixelsHigh: 1024, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.current = ctx
    let g = ctx.cgContext
    g.setShouldAntialias(true); g.interpolationQuality = .high
    [variant1, variant2, variant3][v-1](g)
    return rep
}
func save(_ rep: NSBitmapImageRep, _ path: String) { try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: path)) }

func preview(_ reps: [NSBitmapImageRep], _ path: String) {
    let W = 3*512 + 4*40, H = 512 + 2*40 + 50
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: W, pixelsHigh: H, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!; NSGraphicsContext.current = ctx
    NSColor(calibratedWhite: 0.93, alpha: 1).setFill(); NSRect(x: 0, y: 0, width: W, height: H).fill()
    for (i, r) in reps.enumerated() {
        let x = 40 + i*(512+40)
        NSImage(cgImage: r.cgImage!, size: NSSize(width: 1024, height: 1024)).draw(in: NSRect(x: x, y: 80, width: 512, height: 512))
        let a: [NSAttributedString.Key: Any] = [.font: NSFont.systemFont(ofSize: 30, weight: .semibold), .foregroundColor: NSColor(calibratedWhite: 0.25, alpha: 1)]
        let str = NSAttributedString(string: "\(i+1)", attributes: a)
        str.draw(at: NSPoint(x: CGFloat(x) + 256 - str.size().width/2, y: 28))
    }
    save(rep, path)
}

let args = CommandLine.arguments
guard args.count >= 3 else { print("usage: make_icon.swift <1|2|3|all> <out>"); exit(1) }
if args[1] == "all" {
    let dir = args[2]; let reps = (1...3).map(render)
    for (i, r) in reps.enumerated() { save(r, "\(dir)/variant-\(i+1).png") }
    preview(reps, "\(dir)/variants-preview.png")
} else if let v = Int(args[1]), (1...3).contains(v) { save(render(v), args[2]) }
