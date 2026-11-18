#!/usr/bin/env python3
"""Render docs/assets/og/og-<lang>.png (1200x630) with headless Chrome, then
compress the PNGs LOSSLESSLY (pixels identical, no quantization).

Usage:
  python3 site/og.py                       render all languages + optimize
  python3 site/og.py --out-dir DIR         render into DIR instead of docs/assets/og
  python3 site/og.py --optimize-only [FILES...]
        only optimize existing PNGs (default: docs/assets/og/*.png), no re-render,
        e.g. python3 site/og.py --optimize-only docs/assets/*.png

Optimizer, first one found: oxipng (-o max --strip safe --alpha), zopflipng,
optipng (-o7 -strip all), else a lossless magick filter sweep (keeps the smallest).
After optimizing, decoded pixels are compared with `magick compare -metric AE`;
if they differ (or the result is not smaller) the original file is kept.
Needs Google Chrome for rendering; `brew install oxipng` gives the best results.
Run it when titles/meta lines change, then run site/build.py."""
import argparse, base64, pathlib, shutil, subprocess, sys, tempfile
from html import escape as e
from translations import T, ORDER, OG_META

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "og"
ICON = ROOT / "Resources" / "icon" / "AppIcon-1024.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

HTML = """<!doctype html><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0}
html,body{width:1200px;height:630px;overflow:hidden}
body{font-family:-apple-system,"SF Pro Display","Helvetica Neue",Arial,sans-serif;color:#0b1f3a;
 background:radial-gradient(circle at 50% 38%,#e3f0ff 0,#f2f8ff 45%,#fbfdff 100%);
 display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.icon{width:236px;height:236px;margin-bottom:26px;position:relative}
.icon:before{content:"";position:absolute;inset:-60px;background:radial-gradient(closest-side,rgba(10,132,255,.38),rgba(10,132,255,0));z-index:0}
.icon img{position:relative;width:100%;height:100%;filter:drop-shadow(0 18px 24px rgba(20,60,120,.28))}
.name{font-size:34px;font-weight:600;letter-spacing:.2px;color:#0a6cdf;margin-bottom:10px}
h1{font-size:60px;line-height:1.08;font-weight:700;letter-spacing:-1px;max-width:820px}
.meta{margin-top:22px;font-size:25px;color:#4a6285;font-weight:500}
</style><div class="icon"><img src="data:image/png;base64,@ICON@"></div>
<div class="name">LangSwitcher</div><h1>@H1@</h1><div class="meta">@META@</div>"""

def _run(cmd):
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def _candidates(src, tmp):
    """Yield (tool, path) of lossless re-encodings of src written in tmp dir."""
    n = [0]
    def out():
        n[0] += 1
        return tmp / f"c{n[0]}.png"
    if shutil.which("oxipng"):
        o = out(); shutil.copy(src, o)
        if _run(["oxipng", "-o", "max", "--strip", "safe", "--alpha", "-q", str(o)]):
            yield "oxipng", o
    elif shutil.which("zopflipng"):
        o = out()
        if _run(["zopflipng", "-y", "--iterations=15", "--filters=01234mepb", str(src), str(o)]):
            yield "zopflipng", o
    elif shutil.which("optipng"):
        o = out()
        if _run(["optipng", "-o7", "-strip", "all", "-quiet", "-out", str(o), str(src)]):
            yield "optipng", o
    elif shutil.which("magick"):
        # lossless re-encode only: filter sweep x zlib strategy, caller keeps the smallest
        for flt in range(6):
            for strat in (0, 1):
                o = out()
                if _run(["magick", str(src), "-strip", "-define", "png:compression-level=9",
                         "-define", f"png:compression-filter={flt}",
                         "-define", f"png:compression-strategy={strat}", f"PNG32:{o}"]):
                    yield "magick", o

def same_pixels(a, b):
    r = subprocess.run(["magick", "compare", "-metric", "AE", str(a), str(b), "null:"],
                       capture_output=True, text=True)
    txt = (r.stderr or r.stdout).strip().split()
    return bool(txt) and txt[0] == "0"

def optimize(path):
    path = pathlib.Path(path)
    before = path.stat().st_size
    if not shutil.which("magick"):
        print(f"WARN {path}: magick missing, cannot verify pixels; skipped"); return
    with tempfile.TemporaryDirectory() as d:
        best, tool = None, None
        for t, c in _candidates(path, pathlib.Path(d)):
            if c.stat().st_size < (best.stat().st_size if best else before):
                best, tool = c, t
        if best is None:
            print(f"{path}: {before} B, no smaller lossless result"); return
        if not same_pixels(path, best):
            print(f"WARN {path}: pixels differ after {tool}, original kept"); return
        shutil.copy(best, path)
    after = path.stat().st_size
    print(f"{path}: {tool}  {before} -> {after} B ({100 * (before - after) / before:.1f}% smaller, pixels identical)")

def main():
    ap = argparse.ArgumentParser(description="Render OG images and compress them losslessly.")
    ap.add_argument("--optimize-only", action="store_true", help="skip rendering, only optimize PNGs")
    ap.add_argument("--out-dir", type=pathlib.Path, default=OUT, help="render output dir")
    ap.add_argument("files", nargs="*", type=pathlib.Path, help="PNGs for --optimize-only")
    args = ap.parse_args()
    if args.optimize_only:
        for f in (args.files or sorted(OUT.glob("*.png"))):
            optimize(f)
        return
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    icon = base64.b64encode(ICON.read_bytes()).decode()
    tmp = pathlib.Path(tempfile.mkdtemp())
    for l in ORDER:
        f = tmp / f"{l}.html"
        f.write_text(HTML.replace("@ICON@", icon).replace("@H1@", e(T[l]["h1"])).replace("@META@", e(OG_META[l])), encoding="utf-8")
        out = out_dir / f"og-{l}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--window-size=1200,630",
                        f"--screenshot={out}", f.as_uri()], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        optimize(out)

if __name__ == "__main__":
    main()
