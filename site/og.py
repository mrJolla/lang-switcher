#!/usr/bin/env python3
"""Render docs/assets/og/og-<lang>.png (1200x630) with headless Chrome.
Usage: python3 site/og.py   (needs Google Chrome; optimizes with magick if present)
Run it when titles/meta lines change, then run site/build.py."""
import base64, pathlib, shutil, subprocess, tempfile
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

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icon = base64.b64encode(ICON.read_bytes()).decode()
    tmp = pathlib.Path(tempfile.mkdtemp())
    for l in ORDER:
        f = tmp / f"{l}.html"
        f.write_text(HTML.replace("@ICON@", icon).replace("@H1@", e(T[l]["h1"])).replace("@META@", e(OG_META[l])), encoding="utf-8")
        out = OUT / f"og-{l}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--window-size=1200,630",
                        f"--screenshot={out}", f.as_uri()], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if shutil.which("magick"):  # strip metadata, max compression
            subprocess.run(["magick", str(out), "-strip", "-define", "png:compression-level=9",
                            f"PNG24:{out}"], check=True)
        print(out.relative_to(ROOT), out.stat().st_size // 1024, "KB")

if __name__ == "__main__":
    main()
