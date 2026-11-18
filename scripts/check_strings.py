#!/usr/bin/env python3
"""Key parity check for Resources/*.lproj/Localizable.strings (run by `make test`).
Fails if: plutil -lint fails, a language misses/has extra keys vs en, %@ placeholders differ,
a key used in Sources/ is absent from en, or lproj set != CFBundleLocalizations in Info.plist."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
files = sorted((ROOT / "Resources").glob("*.lproj/Localizable.strings"))
errors = []
def load(p):
    r = subprocess.run(["plutil", "-lint", str(p)], capture_output=True, text=True)
    if r.returncode: errors.append(f"{p.parent.name}: plutil -lint failed: {r.stdout.strip()}{r.stderr.strip()}"); return None
    return json.loads(subprocess.run(["plutil", "-convert", "json", "-o", "-", str(p)], capture_output=True, text=True, check=True).stdout)
data = {p.parent.name[:-6]: load(p) for p in files}
base = data.get("en")
if base is None: errors.append("en.lproj missing or invalid")
else:
    for lang, d in data.items():
        if d is None or lang == "en": continue
        for k in sorted(base.keys() - d.keys()): errors.append(f"{lang}: missing key {k}")
        for k in sorted(d.keys() - base.keys()): errors.append(f"{lang}: extra key {k}")
        for k in base.keys() & d.keys():
            if base[k].count("%@") != d[k].count("%@"): errors.append(f"{lang}: placeholder mismatch in {k}")
        for k, v in d.items():
            if not v.strip(): errors.append(f"{lang}: empty value for {k}")
    used = set()
    for s in (ROOT / "Sources").rglob("*.swift"):
        used |= set(re.findall(r'NSLocalizedString\("([^"]+)"', s.read_text(encoding="utf-8")))
    for k in sorted(used - base.keys()): errors.append(f"en: key used in code but not defined: {k}")
    for k in sorted(base.keys() - used): errors.append(f"en: key defined but unused in code: {k}")
info = json.loads(subprocess.run(["plutil", "-convert", "json", "-o", "-", str(ROOT / "Info.plist")], capture_output=True, text=True, check=True).stdout)
if sorted(info.get("CFBundleLocalizations", [])) != sorted(data): errors.append(f"CFBundleLocalizations {sorted(info.get('CFBundleLocalizations', []))} != lproj {sorted(data)}")
if info.get("CFBundleDevelopmentRegion") != "en": errors.append("CFBundleDevelopmentRegion must be en")
if errors:
    print("strings check FAILED"); [print("  -", e) for e in errors]; sys.exit(1)
print(f"strings check OK: {len(data)} languages ({', '.join(sorted(data))}), {len(base)} keys each")
