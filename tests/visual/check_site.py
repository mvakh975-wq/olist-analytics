"""Open every dashboard page at desktop and phone widths in light and dark mode.

Fails on console errors, page errors, error messages rendered by the page, horizontal scroll,
a missing lang attribute or missing link-preview tags,
and saves a full-page screenshot of each combination.

Usage: python tests/visual/check_site.py BASE_URL OUT_DIR
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGES = ["", "growth", "retention", "customers", "delivery", "methodology"]
VIEWPORTS = {"desktop": (1440, 900), "phone": (390, 844)}


def main(base: str, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vp, (w, h) in VIEWPORTS.items():
            for scheme in ("light", "dark"):
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                page = ctx.new_page()
                errors = []
                page.on("console", lambda m, e=errors: m.type == "error" and e.append(m.text))
                page.on("pageerror", lambda exc, e=errors: e.append(str(exc)))
                for slug in PAGES:
                    name = slug or "index"
                    page.goto(f"{base.rstrip('/')}/{slug}", wait_until="networkidle")
                    page.wait_for_timeout(2500)
                    # Framework renders cell errors inline with this class
                    for text in page.locator(".observablehq--error").all_inner_texts():
                        problems.append(f"{vp}/{scheme}/{name}: {text.strip()[:200]}")
                    if page.evaluate("document.documentElement.lang") != "en":
                        problems.append(f"{vp}/{scheme}/{name}: <html> has no lang=en")
                    for tag in ("og:title", "og:description", "og:image"):
                        if not page.locator(f'meta[property="{tag}"]').count():
                            problems.append(f"{vp}/{scheme}/{name}: missing {tag}")
                    if page.evaluate(
                        "document.documentElement.scrollWidth > window.innerWidth + 1"
                    ):
                        problems.append(f"{vp}/{scheme}/{name}: horizontal scroll")
                    page.screenshot(path=out / f"{name}-{vp}-{scheme}.png", full_page=True)
                problems += [f"{vp}/{scheme}: {e}" for e in errors]
                ctx.close()
        browser.close()
    print("\n".join(problems) or "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], Path(sys.argv[2])))
