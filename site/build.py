#!/usr/bin/env python3
"""Generate docs/<lang>/index.html, docs/index.html, docs/404.html, docs/robots.txt, docs/sitemap.xml.
Usage: python3 site/build.py   (no dependencies)
Social images docs/assets/og/og-<lang>.png are made separately by: python3 site/og.py (needs Chrome)."""
import datetime, json, pathlib, re
from html import escape as e
from translations import T, S, ORDER, VERSION, OG_META

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "https://mrjolla.github.io/lang-switcher/"
REPO = "https://github.com/mrJolla/lang-switcher"
DMG = REPO + "/releases/latest/download/LangSwitcher.dmg"
def bcp(l): return T[l].get("bcp", l)   # hreflang / html lang / JSON-LD (pt -> pt-BR); URL path stays /pt/

# The app's own menu labels come from the .strings files, so the site mockups can't drift from the app.
STR_KEYS = {"grant": "menu.grantPermission", "enabled": "menu.enabled", "layouts": "menu.layouts",
            "login": "menu.launchAtLogin", "quit": "menu.quit"}
def app_strings(l):
    path = ROOT / "Resources" / f'{T[l].get("lproj", l)}.lproj' / "Localizable.strings"
    d = {}
    for k, v in re.findall(r'^"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', path.read_text(encoding="utf-8"), re.M):
        d[k] = v.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
    return {name: d[key] for name, key in STR_KEYS.items()}

for _l in ORDER: S[_l]["ui"].update(app_strings(_l))

FLAG = {"ru": "ru", "en": "gb", "de": "de", "es": "es", "it": "it", "fr": "fr", "pt": "pt"}

SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
<symbol id="f-ru" viewBox="0 0 30 20"><rect width="30" height="20" fill="#fff"/><rect y="6.67" width="30" height="6.67" fill="#0039a6"/><rect y="13.33" width="30" height="6.67" fill="#d52b1e"/></symbol>
<symbol id="f-de" viewBox="0 0 30 20"><rect width="30" height="20" fill="#dd0000"/><rect width="30" height="6.67" fill="#000"/><rect y="13.33" width="30" height="6.67" fill="#ffce00"/></symbol>
<symbol id="f-es" viewBox="0 0 30 20"><rect width="30" height="20" fill="#aa151b"/><rect y="5" width="30" height="10" fill="#f1bf00"/></symbol>
<symbol id="f-it" viewBox="0 0 30 20"><rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#009246"/><rect x="20" width="10" height="20" fill="#ce2b37"/></symbol>
<symbol id="f-fr" viewBox="0 0 30 20"><rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#0055a4"/><rect x="20" width="10" height="20" fill="#ef4135"/></symbol>
<symbol id="f-pt" viewBox="0 0 30 20"><rect width="30" height="20" fill="#009c3b"/><path d="M15 1.8 28 10 15 18.2 2 10z" fill="#ffdf00"/><circle cx="15" cy="10" r="4.6" fill="#002776"/></symbol>
<symbol id="f-gb" viewBox="0 0 30 20"><rect width="30" height="20" fill="#012169"/><path d="M0 0L30 20M30 0L0 20" stroke="#fff" stroke-width="4"/><path d="M0 0L30 20M30 0L0 20" stroke="#c8102e" stroke-width="1.6"/><path d="M15 0V20M0 10H30" stroke="#fff" stroke-width="6"/><path d="M15 0V20M0 10H30" stroke="#c8102e" stroke-width="3.6"/></symbol>
</defs></svg>"""

def flag(code):
    return f'<svg class="flag" viewBox="0 0 30 20" width="22" height="15" aria-hidden="true" focusable="false"><use href="#f-{FLAG[code]}"/></svg>'

GH_MARK = '<svg class="gh-mark" viewBox="0 0 16 16" width="20" height="20" aria-hidden="true" focusable="false"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'


DMG_ICON = '<svg class="dmgicon" viewBox="0 0 40 48" width="34" height="41" aria-hidden="true"><defs><linearGradient id="dg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4f5f7"/><stop offset="1" stop-color="#c9ccd2"/></linearGradient></defs><path d="M6 1h20l10 10v33a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V4a3 3 0 0 1 3-3z" fill="url(#dg)" stroke="#9a9ea6" stroke-width="1"/><path d="M26 1v8a2 2 0 0 0 2 2h8" fill="#dfe1e5" stroke="#9a9ea6" stroke-width="1"/><rect x="9" y="26" width="22" height="11" rx="3" fill="#8e939c"/><circle cx="27" cy="31.5" r="1.7" fill="#e8eaee"/></svg>'
FOLDER = '<svg viewBox="0 0 64 52" width="76" height="62" aria-hidden="true"><defs><linearGradient id="fg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6cc4fb"/><stop offset="1" stop-color="#2d8ef0"/></linearGradient></defs><path d="M4 8a4 4 0 0 1 4-4h14l6 6h28a4 4 0 0 1 4 4v30a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#4aa7f5"/><rect x="2" y="14" width="60" height="34" rx="4" fill="url(#fg)"/></svg>'
ARROW = '<svg class="arrow" viewBox="0 0 48 24" width="48" height="24" aria-hidden="true"><path d="M2 12h40M33 3l9 9-9 9" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
LIGHTS = '<span class="lights" aria-hidden="true"><i></i><i></i><i></i></span>'

def sidebar(sel):
    rows = "".join(f'<span class="sk"><i></i><b></b></span>' for _ in range(3))
    return f'<div class="side">{rows}<span class="sk sel"><i></i><span>{e(sel)}</span></span>{rows}</div>'

def mock(n, u):
    ic = "../assets/icon-64.png"
    if n == 1:
        return (f'<div class="mock m1" role="img" aria-label="LangSwitcher.dmg">'
                f'<div class="pop"><div class="pop-h">{e(u["downloads"])}</div>'
                f'<div class="dl">{DMG_ICON}<div><b>LangSwitcher.dmg</b><small>v{VERSION}</small></div>'
                f'<svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6 10l3 3 5-6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div></div>')
    if n == 2:
        return (f'<div class="mock m2" role="img" aria-label="LangSwitcher → {e(u["applications"], True)}">'
                f'<div class="titlebar">{LIGHTS}<span class="ttl">LangSwitcher</span></div>'
                f'<div class="dmgbody"><figure><img src="../assets/icon-256.png" width="84" height="84" alt=""><figcaption>LangSwitcher</figcaption></figure>{ARROW}'
                f'<figure>{FOLDER}<figcaption>{e(u["applications"])}</figcaption></figure></div></div>')
    if n == 3:
        return (f'<div class="mock m3" role="img" aria-label="{e(u["settings"], True)} › {e(u["privacy"], True)}">'
                f'<div class="titlebar">{LIGHTS}</div><div class="pane">{sidebar(u["privacy"])}'
                f'<div class="main"><h4>{e(u["privacy"])}</h4><div class="card"><p>{e(u["blocked"])}</p>'
                f'<span class="pill hl">{e(u["open_anyway"])}</span></div></div></div></div>')
    if n == 4:
        return (f'<div class="mock m4" role="img" aria-label="{e(u["input_mon"], True)}">'
                f'<div class="titlebar">{LIGHTS}</div><div class="pane">{sidebar(u["privacy"])}'
                f'<div class="main"><h4>{e(u["input_mon"])}</h4><div class="card list">'
                f'<div class="row"><span class="ph"></span><b class="skbar"></b><span class="tg"><i></i></span></div>'
                f'<div class="row"><img src="{ic}" width="26" height="26" alt=""><span>LangSwitcher</span><span class="tg on hl"><i></i></span></div>'
                f'</div></div></div></div>')
    return (f'<div class="mock m5" role="img" aria-label="EN">'
            f'<div class="menubar"><span class="sk"><i></i></span><span class="sk"><i></i></span><span class="ind">EN</span><span class="clk"></span></div>'
            f'<ul class="dd"><li><span class="ck">✓</span>{e(u["enabled"])}</li><li><span class="ck"></span>{e(u["layouts"])}<span class="more">›</span></li>'
            f'<li class="sep"></li><li><span class="ck"></span>{e(u["login"])}</li><li class="sep"></li><li><span class="ck"></span>{e(u["quit"])}</li></ul></div>')

def steps(lang):
    s = S[lang]; u = s["ui"]
    items = []
    for i, (ti, tx) in enumerate(s["steps"], 1):
        ti, tx = ti.format(**u), tx.format(**u)
        if i == 1:
            ti = f'<a href="{DMG}">{e(ti)}</a>'
        else:
            ti = e(ti)
        items.append(f'<li class="step"><div class="txt"><span class="num" aria-hidden="true">{i}</span><div><h3>{ti}</h3><p>{e(tx)}</p></div></div><div class="art">{mock(i, u)}</div></li>')
    return f'<section class="install container" aria-labelledby="install-h"><h2 id="install-h">{e(s["h"])}</h2><ol class="steps">' + "".join(items) + '</ol></section>'

TODAY = datetime.date.today().isoformat()

def og_url(l): return f"{BASE}assets/og/og-{l}.png"

def og_alt(l): return T[l]["og_alt"]

def social(l, url, locale, alt_locales):
    """OG + Twitter + theme-color + JSON-LD for page in language l (root uses en)."""
    t = T[l]
    d, n, a = e(t["description"], True), e(t["title"], True), e(og_alt(l), True)
    ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "LangSwitcher",
          "description": t["description"], "operatingSystem": "macOS 13+",
          "applicationCategory": "UtilitiesApplication", "softwareVersion": VERSION,
          "offers": {"@type": "Offer", "price": 0, "priceCurrency": "USD"},
          "downloadUrl": DMG, "image": og_url(l), "url": url, "inLanguage": bcp(l),
          "author": {"@type": "Person", "name": "mrJolla", "url": "https://github.com/mrJolla"}}
    ldj = json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/")
    alts = "\n".join(f'<meta property="og:locale:alternate" content="{T[x]["locale"]}">' for x in alt_locales)
    return f"""<meta name="theme-color" content="#fbfbfd" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:site_name" content="LangSwitcher">
<meta property="og:title" content="{n}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_url(l)}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{a}">
<meta property="og:locale" content="{locale}">
{alts}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{n}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{og_url(l)}">
<meta name="twitter:image:alt" content="{a}">
<script type="application/ld+json">
{ldj}
</script>"""

def page(lang):
    t = T[lang]
    alts = "\n".join(f'<link rel="alternate" hreflang="{bcp(l)}" href="{BASE}{l}/">' for l in ORDER)
    alts += f'\n<link rel="alternate" hreflang="x-default" href="{BASE}">'
    opts = "\n".join(
        f'<li role="none"><a role="menuitem" href="../{l}/" hreflang="{bcp(l)}" lang="{bcp(l)}" data-lang="{l}"'
        f'{" aria-current=\"true\"" if l == lang else ""}>{flag(l)}<span>{e(T[l]["native"])}</span></a></li>'
        for l in ORDER)
    meta = e(t["meta"].format(v=VERSION))
    d, n = e(t["description"], True), e(t["title"], True)
    return f"""<!doctype html>
<html lang="{bcp(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t["title"])}</title>
<meta name="description" content="{d}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="{BASE}{lang}/">
{alts}
{social(lang, BASE + lang + "/", t["locale"], [l for l in ORDER if l != lang])}
<link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32.png">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
{SPRITE}
<header class="site-header">
<div class="bar container">
<a class="brand" href="./" aria-label="{e(t["home"], True)}"><img src="../assets/icon-64.png" width="32" height="32" alt=""><span>LangSwitcher</span></a>
<div class="actions">
<a class="gh-link" href="{REPO}" aria-label="{e(t["gh_label"], True)}">{GH_MARK}<span class="gh-text">GitHub</span></a>
<details class="lang" id="lang">
<summary aria-label="{e(t["lang_label"], True)}">{flag(lang)}<span class="code">{lang}</span><svg class="chev" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>
<ul role="menu" aria-label="{e(t["lang_label"], True)}">
{opts}
</ul>
</details>
</div>
</div>
</header>
<main class="hero container">
<div class="icon-wrap"><img class="app-icon" src="../assets/icon-512.png" srcset="../assets/icon-256.png 256w, ../assets/icon-512.png 512w" sizes="(max-width: 480px) 168px, 216px" width="216" height="216" alt="{e(t["icon_alt"], True)}"></div>
<h1>{e(t["h1"])}</h1>
<p class="sub">{e(t["sub"])}</p>
<div class="buttons">
<a class="btn primary" href="{DMG}">{e(t["download"])}</a>
<a class="btn secondary" href="{REPO}">{e(t["github"])}</a>
</div>
<p class="meta">{meta}</p>
</main>
{steps(lang)}
<footer class="site-footer container">© 2026 mrJolla · <a href="{REPO}">GitHub</a> · <a href="{REPO}/blob/main/LICENSE">{e(t["license"])}</a></footer>
<script src="../assets/lang.js"></script>
</body>
</html>
"""

def root():
    langs = ",".join(f'"{l}"' for l in ORDER)
    links = "\n".join(f'<li><a href="{l}/" hreflang="{bcp(l)}">{e(T[l]["native"])}</a></li>' for l in ORDER)
    alts = "\n".join(f'<link rel="alternate" hreflang="{bcp(l)}" href="{BASE}{l}/">' for l in ORDER)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(T["en"]["title"])}</title>
<meta name="description" content="{e(T["en"]["description"], True)}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="{BASE}">
{alts}
<link rel="alternate" hreflang="x-default" href="{BASE}">
{social("en", BASE, T["en"]["locale"], [l for l in ORDER if l != "en"])}
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="stylesheet" href="assets/style.css">
<script>
(function () {{
  var langs = [{langs}], pick = "en";
  try {{
    var s = localStorage.getItem("lang");
    if (s && langs.indexOf(s) > -1) pick = s;
    else {{
      var n = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"];
      for (var i = 0; i < n.length; i++) {{
        var c = String(n[i]).toLowerCase().split("-")[0];
        if (langs.indexOf(c) > -1) {{ pick = c; break; }}
      }}
    }}
  }} catch (err) {{
    var n2 = navigator.languages || [navigator.language || "en"];
    for (var j = 0; j < n2.length; j++) {{
      var c2 = String(n2[j]).toLowerCase().split("-")[0];
      if (langs.indexOf(c2) > -1) {{ pick = c2; break; }}
    }}
  }}
  location.replace(pick + "/" + location.search + location.hash);
}})();
</script>
</head>
<body class="plain">
<main class="hero container">
<img class="app-icon" src="assets/icon-256.png" width="128" height="128" alt="LangSwitcher">
<h1>LangSwitcher</h1>
<noscript><ul class="lang-list">
{links}
</ul></noscript>
</main>
</body>
</html>
"""

def notfound():
    # Absolute paths: a 404 can be served from any depth under /lang-switcher/.
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 — Page not found · LangSwitcher</title>
<meta name="robots" content="noindex">
<meta name="color-scheme" content="light dark">
<link rel="icon" type="image/png" href="/lang-switcher/assets/favicon-32.png">
<link rel="stylesheet" href="/lang-switcher/assets/style.css">
</head>
<body class="plain">
<main class="hero container">
<img class="app-icon" src="/lang-switcher/assets/icon-256.png" width="128" height="128" alt="LangSwitcher">
<h1>404</h1>
<p class="sub"><a href="/lang-switcher/">LangSwitcher</a></p>
</main>
</body>
</html>
"""

def robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n"

def sitemap():
    def entry(loc):
        links = "".join(f'    <xhtml:link rel="alternate" hreflang="{bcp(l)}" href="{BASE}{l}/"/>\n' for l in ORDER)
        links += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}"/>\n'
        return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{TODAY}</lastmod>\n{links}  </url>\n"
    urls = entry(BASE) + "".join(entry(f"{BASE}{l}/") for l in ORDER)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            f'        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n{urls}</urlset>\n')

def write(path, s):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8")

for l in ORDER:
    write(DOCS / l / "index.html", page(l))
write(DOCS / "index.html", root())
write(DOCS / "404.html", notfound())
write(DOCS / "robots.txt", robots())
write(DOCS / "sitemap.xml", sitemap())
(DOCS / ".nojekyll").touch()
print("built:", ", ".join(ORDER))
