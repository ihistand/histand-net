"""Integration tests for area `site` (docs/prd/histand-net/test-cases/site.yaml).

Every expected value is copied from the PRD's test cases; every reading rule
(how a page is parsed, how text and JSON are compared) is testing.md's
Harness, "Assertions". The tests only read the committed files of the
checkout and run `git check-ignore`; nothing is written.
"""

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # tests/integration/<file> -> the repository root

# A known-failing case (testing-from-prds): the test raises pytest's own
# expected-failure exception only when it sees the case's `symptom:`; the
# strict marker accepts only that exception, so any other failure fails.
KNOWN_FAILURE = pytest.xfail.Exception

# --------------------------------------------------------------------------
# Helpers (testing.md, Harness: Assertions)
# --------------------------------------------------------------------------

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
_ASCII_WS = re.compile(r"[ \t\n\f\r]+")


def norm(s):
    """Collapse each run of ASCII white space to one space and trim it."""
    if s is None:
        return None
    return _ASCII_WS.sub(" ", s).strip(" ")


class Element:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []  # Element or str (text); comments are dropped

    def get(self, name):
        """The attribute's value, entities decoded, or None when absent."""
        return self.attrs.get(name)

    def raw_text(self):
        out = []
        for c in self.children:
            out.append(c if isinstance(c, str) else c.raw_text())
        return "".join(out)

    def text(self):
        return norm(self.raw_text())

    def descendants(self):
        for c in self.children:
            if isinstance(c, Element):
                yield c
                yield from c.descendants()

    def classes(self):
        return (self.get("class") or "").split()


class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, None)
        self.stack = [self.root]
        self.order = []  # every element, in start-tag order

    def _new(self, tag, attrs):
        d = {}
        for k, v in attrs:
            d[k] = "" if v is None else v  # last value wins; no value is ""
        el = Element(tag, d, self.stack[-1])
        self.stack[-1].children.append(el)
        self.order.append(el)
        return el

    def handle_starttag(self, tag, attrs):
        el = self._new(tag, attrs)
        if tag not in VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        self._new(tag, attrs)  # a self-closed tag holds nothing

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # an end tag with no open element of its name is ignored

    def handle_data(self, data):
        self.stack[-1].children.append(data)


class Page:
    def __init__(self, rel_path):
        p = TreeParser()
        p.feed((ROOT / rel_path).read_text(encoding="utf-8"))
        p.close()
        self.order = p.order
        self.root = p.root

    def all(self, tag):
        return [e for e in self.order if e.tag == tag]

    def first(self, tag, pred=lambda e: True):
        for e in self.order:
            if e.tag == tag and pred(e):
                return e
        return None

    def index(self, el):
        return next(i for i, e in enumerate(self.order) if e is el)

    def first_after(self, tag, anchor):
        start = self.index(anchor)
        for e in self.order[start + 1:]:
            if e.tag == tag:
                return e
        return None

    def h2(self, text):
        return self.first("h2", lambda e: e.text() == text)

    def body_text(self):
        body = self.first("body")
        assert body is not None, "the file has no body element"
        return body.text()

    def style_texts(self):
        return [e.text() for e in self.all("style")]

    def json_ld(self):
        s = self.first("script", lambda e: e.get("type") == "application/ld+json")
        assert s is not None, "the file has no script element of type application/ld+json"
        return json.loads(s.raw_text())


def rel_holds(el, word):
    rel = el.get("rel")
    if rel is None:
        return False
    return word.lower() in [t.lower() for t in rel.split(" ") if t]


def meta_value(page, key):
    el = page.first("meta", lambda e: e.get("name") == key or e.get("property") == key)
    return None if el is None else norm(el.get("content"))


def link_of(el):
    a = next((d for d in el.descendants() if d.tag == "a"), None)
    if a is None:
        return None
    return {"text": a.text(), "href": norm(a.get("href"))}


def strict_eq(a, b):
    """Data equality with no white space collapsed and no bool/int mixing."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, dict):
        return (isinstance(b, dict) and a.keys() == b.keys()
                and all(strict_eq(a[k], b[k]) for k in a))
    if isinstance(a, list):
        return (isinstance(b, list) and len(a) == len(b)
                and all(strict_eq(x, y) for x, y in zip(a, b)))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b


def data_matches(case, actual):
    """testing.md "Compared as data": a mapping compares the keys the case lists;
    a list compares whole and in order; a mapping inside a list compares whole."""
    if isinstance(case, dict):
        return isinstance(actual, dict) and all(
            k in actual and data_matches(v, actual[k]) for k, v in case.items())
    if isinstance(case, list):
        return (isinstance(actual, list) and len(case) == len(actual)
                and all(strict_eq(c, a) if isinstance(c, dict) else data_matches(c, a)
                        for c, a in zip(case, actual)))
    return strict_eq(case, actual)


def load_json(rel_path):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def read_text(rel_path):
    return (ROOT / rel_path).read_bytes().decode("utf-8")


def holds_word(text, word):
    """True when `word` occurs with no letter or digit right before or after it."""
    start = 0
    while True:
        i = text.find(word, start)
        if i < 0:
            return False
        before = text[i - 1] if i > 0 else ""
        j = i + len(word)
        after = text[j] if j < len(text) else ""
        if not (before and before.isalnum()) and not (after and after.isalnum()):
            return True
        start = i + 1


def list_items_after_h2(page, h2_text):
    h2 = page.h2(h2_text)
    assert h2 is not None, f"no h2 reading {h2_text!r}"
    ul = page.first_after("ul", h2)
    assert ul is not None, f"no ul after the h2 {h2_text!r}"
    return ul, [c for c in ul.children if isinstance(c, Element) and c.tag == "li"]


def read_item(li, case_item):
    """Read an li as the keys the case item names."""
    got = {}
    if "link" in case_item:
        got["link"] = link_of(li)
    if "icon" in case_item:
        img = next((d for d in li.descendants() if d.tag == "img"), None)
        got["icon"] = "none" if img is None else norm(img.get("src"))
    if "desc-not-empty" in case_item:
        got["desc-not-empty"] = any(
            d.tag == "span" and "desc" in d.classes() and d.text() != ""
            for d in li.descendants())
    return got


def assert_list_after_h2(page, h2_text, items, every_icon=None):
    ul, lis = list_items_after_h2(page, h2_text)
    got = [read_item(li, it) for li, it in zip(lis, items)]
    assert len(lis) == len(items), f"{len(lis)} li items after h2 {h2_text!r}, expected {len(items)}: {got}"
    assert got == items
    if every_icon is not None:
        for img in (d for d in ul.descendants() if d.tag == "img"):
            for k, v in every_icon.items():
                assert norm(img.get(k)) == v, f"img {img.attrs} has {k}={img.get(k)!r}, expected {v!r}"


def assert_head(page, expected):
    html = page.first("html")
    assert html is not None and norm(html.get("lang")) == expected["html-lang"]
    charset = page.first("meta", lambda e: e.get("charset") is not None)
    assert charset is not None and norm(charset.get("charset")) == expected["meta-charset"]
    title = page.first("title")
    assert title is not None and title.text() == expected["title"]
    for k, v in expected["meta"].items():
        assert meta_value(page, k) == v, f"meta {k}: {meta_value(page, k)!r}, expected {v!r}"
    canon = page.first("link", lambda e: rel_holds(e, "canonical"))
    assert canon is not None and norm(canon.get("href")) == expected["link-canonical"]


def assert_meta(page, expected):
    for k, v in expected.items():
        assert meta_value(page, k) == v, f"meta {k}: {meta_value(page, k)!r}, expected {v!r}"


def icon_links(page):
    return [e for e in page.all("link")
            if rel_holds(e, "icon") or rel_holds(e, "apple-touch-icon") or rel_holds(e, "manifest")]


def assert_icon_links(page, items):
    links = icon_links(page)
    got = [dict(e.attrs) for e in links]
    assert len(links) == len(items), f"{len(links)} icon links, expected {len(items)}: {got}"
    for el, item in zip(links, items):
        for k, v in item.items():
            if k.endswith("-begins"):
                attr = k[: -len("-begins")]
                val = norm(el.get(attr))
                assert val is not None and val.startswith(v), f"{attr}={val!r} does not begin {v!r}"
            else:
                assert norm(el.get(k)) == v, f"link {el.attrs}: {k}={el.get(k)!r}, expected {v!r}"


_ASCII_WS_CHARS = " \t\n\f\r"


def _rel_tokens_hold(el, word):
    """`rel` holds a word: one of its white-space-separated tokens, any letter case."""
    rel = el.get("rel")
    if rel is None:
        return False
    return word.lower() in [t.lower() for t in _ASCII_WS.split(rel) if t]


def is_local_reference(value):
    """testing.md Assertions, `loaded-references-local`: trimmed, the value is `/`
    alone, or starts with `/` and a second character that is not `/`, or starts
    with `data:`."""
    if value is None:
        return False
    v = value.strip(_ASCII_WS_CHARS)
    if v == "/":
        return True
    if len(v) >= 2 and v[0] == "/" and v[1] != "/":
        return True
    return v.startswith("data:")


def assert_loaded_references_local(page):
    refs = [e.get("src") for e in page.all("img")]
    refs += [e.get("href") for e in page.all("link")
             if any(_rel_tokens_hold(e, w) for w in ("icon", "apple-touch-icon", "manifest", "stylesheet"))]
    bad = [r for r in refs if not is_local_reference(r)]
    assert bad == [], f"references not local: {bad}"


def assert_style_none_of(page, values):
    for t in page.style_texts():
        for v in values:
            assert v not in t, f"a style element holds {v!r}"


def assert_style_holds(page, values):
    style = page.first("style")
    assert style is not None, "the file has no style element"
    t = style.text()
    for v in values:
        assert v in t, f"the first style element does not hold {v!r}"


def script_elements(page):
    return [{"type": e.get("type"), "src": "none" if e.get("src") is None else e.get("src")}
            for e in page.all("script")]


def theme_colors(page):
    return [{"content": norm(e.get("content")), "media": norm(e.get("media"))}
            for e in page.all("meta") if e.get("name") == "theme-color"]


def git_ignored(path):
    r = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert r.returncode in (0, 1), f"git check-ignore {path} exited {r.returncode}: {r.stderr!r}"
    return r.returncode == 0


def redirects():
    data = load_json("vercel.json")
    assert isinstance(data.get("redirects"), list), "vercel.json has no redirects array"
    return data["redirects"]


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_T001_2_family_html_and_no_index_html():
    """@prd T-001.2"""
    assert (ROOT / "family.html").is_file()
    assert not (ROOT / "index.html").is_file()


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason="E-005: README.md names no family.html, and still says Single-page, index.html and 301")
def test_T001_3_readme_describes_the_site():
    """@prd T-001.3 known-failing E-005"""
    text = read_text("README.md")
    missing = [v for v in ["family.html", "https://histand.net/", "308"] if v not in text]
    present = [v for v in ["index.html", "Single-page", "301"] if v in text]
    if not missing and not present:
        return
    symptom = ("family.html" not in text and "Single-page" in text
               and "index.html" in text and "301" in text)
    if symptom:
        pytest.xfail("E-005: README.md names no family.html, and still says Single-page, index.html and 301")
    raise AssertionError(
        f"not the known failure: README.md lacks {missing} and holds {present}")


def test_T002_2_rewrites():
    """@prd T-002.2"""
    expected = {"rewrites": [
        {"source": "/", "has": [{"type": "host", "value": "ivan.histand.net"}], "destination": "/ivan"},
        {"source": "/", "destination": "/family"},
    ]}
    actual = load_json("vercel.json")
    assert data_matches(expected, actual), f"rewrites: {actual.get('rewrites')!r}"


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason="E-005: README.md holds neither ivan.html nor https://ivan.histand.net/")
def test_T002_3_readme_names_the_name_card():
    """@prd T-002.3 known-failing E-005"""
    text = read_text("README.md")
    missing = [v for v in ["ivan.html", "https://ivan.histand.net/"] if v not in text]
    if not missing:
        return
    if "ivan.html" not in text and "https://ivan.histand.net/" not in text:
        pytest.xfail("E-005: README.md holds neither ivan.html nor https://ivan.histand.net/")
    raise AssertionError(f"not the known failure: README.md lacks {missing}")


def test_T003_2_clean_urls():
    """@prd T-003.2"""
    actual = load_json("vercel.json")
    assert data_matches({"cleanUrls": True}, actual), f"cleanUrls: {actual.get('cleanUrls')!r}"


def test_T004_2_family_redirect():
    """@prd T-004.2"""
    reds = redirects()
    for item in [{"source": "/family", "destination": "/", "permanent": True}]:
        assert any(strict_eq(item, r) for r in reds), f"no redirect equal to {item!r}"


def test_T005_2_ivan_redirect():
    """@prd T-005.2"""
    reds = redirects()
    item = {"source": "/ivan", "has": [{"type": "host", "value": "histand.net"}],
            "destination": "https://ivan.histand.net/", "permanent": True}
    assert any(strict_eq(item, r) for r in reds), f"no redirect equal to {item!r}"


ALIAS_HOSTS = [
    "www.histand.net", "histand.com", "www.histand.com", "histand.org", "www.histand.org",
    "histands.com", "www.histands.com", "histands.net", "www.histands.net", "histands.org",
    "www.histands.org", "anilak.net", "www.anilak.net", "hinault.net", "www.hinault.net",
    "ivanivan.net", "www.ivanivan.net",
]


def test_T006_3_alias_redirects():
    """@prd T-006.3"""
    reds = redirects()
    assert len(reds) == 19, f"{len(reds)} redirects, expected 19"
    missing = []
    for host in ALIAS_HOSTS:
        item = {"source": "/:path(.*)", "has": [{"type": "host", "value": host}],
                "destination": "https://histand.net/:path", "permanent": True}
        if not any(data_matches(item, r) for r in reds):
            missing.append(host)
    assert missing == [], f"no matching redirect for hosts {missing}"


ROBOTS = "User-agent: *\nAllow: /\n\nSitemap: https://histand.net/sitemap.xml\n"


def test_T007_2_robots_txt():
    """@prd T-007.2"""
    assert read_text("robots.txt") == ROBOTS


def test_T008_1_sitemap():
    """@prd T-008.1"""
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    assert root.tag == ns + "urlset"

    def child_text(el, name):
        c = el.find(ns + name)
        return None if c is None or c.text is None else c.text.strip()

    urls = [{"loc": child_text(u, "loc"), "lastmod": child_text(u, "lastmod")}
            for u in root if u.tag == ns + "url"]
    assert urls == [
        {"loc": "https://histand.net/", "lastmod": "2026-09-17"},
        {"loc": "https://ivan.histand.net/", "lastmod": "2026-09-17"},
    ]


MANIFEST = {
    "name": "Ivan Histand",
    "short_name": "Histand",
    "start_url": "/",
    "display": "browser",
    "background_color": "#f5f1ea",
    "theme_color": "#f5f1ea",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}


def test_T009_1_manifest():
    """@prd T-009.1"""
    actual = load_json("site.webmanifest")
    assert data_matches(MANIFEST, actual), f"site.webmanifest: {actual!r}"


def test_T010_1_gitignore():
    """@prd T-010.1"""
    ignored = [".vercel", ".vercel/project.json", ".DS_Store", "icons/.DS_Store",
               ".env", ".env.local", ".env.production"]
    not_ignored = ["family.html", "ivan.html", "vercel.json", "robots.txt",
                   "sitemap.xml", "site.webmanifest"]
    wrong = [p for p in ignored if not git_ignored(p)]
    wrong += [p for p in not_ignored if git_ignored(p)]
    assert wrong == [], f"wrongly ignored or not ignored: {wrong}"


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason="E-006: the repository root holds no .vercelignore file")
def test_T010_3_vercelignore_exists():
    """@prd T-010.3 known-failing E-006"""
    path = ROOT / ".vercelignore"
    if path.is_file():
        return
    if not path.exists():
        pytest.xfail("E-006: the repository root holds no .vercelignore file")
    raise AssertionError("not the known failure: .vercelignore exists but is not a file")


FAMILY_TITLE = "Histand — a family name in Doylestown, Bucks County"


def test_T011_1_family_head():
    """@prd T-011.1"""
    assert_head(Page("family.html"), {
        "html-lang": "en",
        "meta-charset": "utf-8",
        "title": FAMILY_TITLE,
        "meta": {
            "viewport": "width=device-width, initial-scale=1",
            "description": "Histand, also written Hiestand: a Mennonite family name long associated with Doylestown and Bucks County, Pennsylvania.",
            "robots": "index, follow",
        },
        "link-canonical": "https://histand.net/",
    })


def test_T012_1_family_share_card():
    """@prd T-012.1"""
    assert_meta(Page("family.html"), {
        "og:type": "website",
        "og:site_name": "Histand",
        "og:title": FAMILY_TITLE,
        "og:description": "A Mennonite family name long associated with Doylestown and Bucks County, Pennsylvania.",
        "og:url": "https://histand.net/",
        "og:locale": "en_US",
        "og:image": "https://histand.net/og-family.png",
        "og:image:width": "1200",
        "og:image:height": "630",
        "og:image:alt": "Histand — a Mennonite family name in Doylestown, Bucks County, PA",
        "twitter:card": "summary_large_image",
        "twitter:title": FAMILY_TITLE,
        "twitter:description": "A Mennonite family name long associated with Doylestown and Bucks County, Pennsylvania.",
        "twitter:image": "https://histand.net/og-family.png",
    })


def test_T013_1_family_json_ld():
    """@prd T-013.1"""
    expected = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": FAMILY_TITLE,
        "url": "https://histand.net/",
        "description": "Histand, also written Hiestand: a Mennonite family name long associated with Doylestown and Bucks County, Pennsylvania.",
        "inLanguage": "en-US",
        "about": {"@type": "Thing", "name": "Histand family",
                  "description": "A Mennonite family of Doylestown Township, Bucks County, Pennsylvania"},
    }
    actual = Page("family.html").json_ld()
    assert data_matches(expected, actual), f"JSON-LD: {actual!r}"


def test_T014_1_family_headings():
    """@prd T-014.1"""
    page = Page("family.html")
    assert [e.text() for e in page.all("h1")] == ["Histand"]
    assert [e.text() for e in page.all("h2")] == [
        "Coming to Doylestown", "Places", "William L. Histand, photographer", "Sources", "This site"]


def test_T014_2_family_sources():
    """@prd T-014.2"""
    assert_list_after_h2(Page("family.html"), "Sources", [
        {"link": {"text": "Mennonite Heritage Center",
                  "href": "https://mhep.org/new-acquisition-joshua-histand-and-enos-gehman-papers/"},
         "desc-not-empty": True},
        {"link": {"text": "Mennonite Heritage Center",
                  "href": "https://mhep.org/from-sandy-ridge-and-pine-run-to-main-street-and-cross-keys-the-photography-of-william-histand-of-doylestown/"},
         "desc-not-empty": True},
        {"link": {"text": "Bucks County Herald",
                  "href": "https://www.buckscountyherald.com/opinion/history-lives-samuel-and-rebecca-histand-house/article_4d711655-2aba-5eb9-9053-f5d3143ebf7c.html"},
         "desc-not-empty": True},
    ])


def test_T014_3_family_this_site_paragraph():
    """@prd T-014.3"""
    page = Page("family.html")
    h2 = page.h2("This site")
    assert h2 is not None, "no h2 reading 'This site'"
    p = page.first_after("p", h2)
    assert p is not None, "no p after the h2 'This site'"
    links = [{"text": a.text(), "href": norm(a.get("href"))} for a in p.descendants() if a.tag == "a"]
    assert links == [{"text": "ivan.histand.net", "href": "https://ivan.histand.net/"}]


def test_T015_1_ivan_head():
    """@prd T-015.1"""
    assert_head(Page("ivan.html"), {
        "html-lang": "en",
        "meta-charset": "utf-8",
        "title": "Ivan Histand",
        "meta": {
            "viewport": "width=device-width, initial-scale=1",
            "description": "Ivan Histand — software I build and how to reach me.",
            "author": "Ivan Histand",
            "robots": "index, follow",
        },
        "link-canonical": "https://ivan.histand.net/",
    })


def test_T016_1_ivan_share_card():
    """@prd T-016.1"""
    assert_meta(Page("ivan.html"), {
        "og:type": "website",
        "og:site_name": "Ivan Histand",
        "og:title": "Ivan Histand",
        "og:description": "Software I build and how to reach me.",
        "og:url": "https://ivan.histand.net/",
        "og:locale": "en_US",
        "og:image": "https://ivan.histand.net/og.png",
        "og:image:width": "1200",
        "og:image:height": "630",
        "og:image:alt": "Ivan Histand — data engineering, and tools for the people who do it.",
        "twitter:card": "summary_large_image",
        "twitter:title": "Ivan Histand",
        "twitter:description": "Software I build and how to reach me.",
        "twitter:image": "https://ivan.histand.net/og.png",
    })


def test_T017_1_ivan_json_ld():
    """@prd T-017.1"""
    expected = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Ivan Histand",
        "url": "https://ivan.histand.net/",
        "email": "mailto:ivan@histand.net",
        "description": "Data engineering, and tools for the people who do it.",
        "worksFor": {
            "@type": "Organization",
            "url": "https://acuantia.com",
            "parentOrganization": {"@type": "Organization", "url": "https://rotoplas.com"},
        },
        "sameAs": ["https://github.com/ihistand"],
    }
    actual = Page("ivan.html").json_ld()
    assert data_matches(expected, actual), f"JSON-LD: {actual!r}"


def test_T017_2_ivan_json_ld_values_in_body_text():
    """@prd T-017.2"""
    page = Page("ivan.html")
    ld = page.json_ld()
    body = page.body_text()
    for path in ["jobTitle", "worksFor.name", "worksFor.parentOrganization.name", "email"]:
        value = ld
        for key in path.split("."):
            assert isinstance(value, dict) and key in value, f"JSON-LD has no {path}"
            value = value[key]
        assert isinstance(value, str), f"JSON-LD {path} is not a string: {value!r}"
        if path == "email" and value.startswith("mailto:"):
            value = value[len("mailto:"):]
        assert value in body, f"the body text does not hold {path} {value!r}"


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason='E-004: knowsAbout also holds "Developer tools"')
def test_T017_3_ivan_knows_about():
    """@prd T-017.3 known-failing E-004"""
    actual = Page("ivan.html").json_ld()
    topics = ["Data engineering", "SQL", "BigQuery", "Dataform", "PostgreSQL"]
    if data_matches({"knowsAbout": topics}, actual):
        return
    got = actual.get("knowsAbout") if isinstance(actual, dict) else None
    # "also holds": the expected topics, and "Developer tools" besides them.
    if (isinstance(got, list) and "Developer tools" in got
            and data_matches(topics, [t for t in got if t != "Developer tools"])):
        pytest.xfail('E-004: knowsAbout also holds "Developer tools"')
    raise AssertionError(f"not the known failure: knowsAbout is {got!r}")


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason='E-004: the visible text holds "Postgres" as a word of its own')
def test_T017_4_ivan_says_postgresql():
    """@prd T-017.4 known-failing E-004"""
    body = Page("ivan.html").body_text()
    has_postgresql = "PostgreSQL" in body
    has_postgres_word = holds_word(body, "Postgres")
    if has_postgresql and not has_postgres_word:
        return
    if has_postgres_word:
        pytest.xfail('E-004: the visible text holds "Postgres" as a word of its own')
    raise AssertionError("not the known failure: the body text does not hold 'PostgreSQL'")


def test_T018_1_ivan_headings_and_lede():
    """@prd T-018.1"""
    page = Page("ivan.html")
    assert [e.text() for e in page.all("h1")] == ["Ivan Histand"]
    lede = page.first("p", lambda e: "lede" in e.classes())
    assert lede is not None and lede.text() == "Data engineering, and tools for the people who do it."
    assert [e.text() for e in page.all("h2")] == ["Projects", "Work", "Elsewhere", "Contact"]


ICON_ATTRS = {"alt": "", "width": "18", "height": "18"}


def test_T018_2_ivan_projects():
    """@prd T-018.2"""
    assert_list_after_h2(Page("ivan.html"), "Projects", [
        {"icon": "/icons/sqlanvil.svg", "link": {"text": "SQLAnvil", "href": "https://sqlanvil.com"}, "desc-not-empty": True},
        {"icon": "/icons/incise.png", "link": {"text": "Incise", "href": "https://incise.dev"}, "desc-not-empty": True},
        {"icon": "/icons/checklists.png", "link": {"text": "Checklists.io", "href": "https://checklists.io"}, "desc-not-empty": True},
        {"icon": "/icons/listanvil.png", "link": {"text": "ListAnvil", "href": "https://listanvil.com"}, "desc-not-empty": True},
        {"icon": "/icons/graver.png", "link": {"text": "Graver", "href": "https://graver.dev"}, "desc-not-empty": True},
        {"icon": "/icons/claude-skills.png", "link": {"text": "Claude Skills", "href": "https://github.com/ihistand/claude-skills"}, "desc-not-empty": True},
    ], every_icon=ICON_ATTRS)


def test_T018_3_ivan_work():
    """@prd T-018.3"""
    assert_list_after_h2(Page("ivan.html"), "Work", [
        {"icon": "/icons/acuantia.png", "link": {"text": "Acuantia", "href": "https://acuantia.com"}, "desc-not-empty": True},
        {"icon": "/icons/rotoplas.png", "link": {"text": "Rotoplas", "href": "https://rotoplas.com"}, "desc-not-empty": True},
    ], every_icon=ICON_ATTRS)


def test_T018_4_ivan_elsewhere():
    """@prd T-018.4"""
    assert_list_after_h2(Page("ivan.html"), "Elsewhere", [
        {"icon": "none", "link": {"text": "histand.net", "href": "https://histand.net/"}, "desc-not-empty": True},
    ])


def test_T018_5_ivan_contact_links():
    """@prd T-018.5"""
    page = Page("ivan.html")
    p = page.first("p", lambda e: "contact" in e.classes())
    assert p is not None, "no p element with class contact"
    links = [{"text": a.text(), "href": norm(a.get("href"))} for a in p.descendants() if a.tag == "a"]
    assert links == [
        {"text": "ivan@histand.net", "href": "mailto:ivan@histand.net"},
        {"text": "ihistand@acuantia.com", "href": "mailto:ihistand@acuantia.com"},
        {"text": "github.com/ihistand", "href": "https://github.com/ihistand"},
        {"text": "linkedin.com/in/ihistand", "href": "https://www.linkedin.com/in/ihistand/"},
    ]


ICON_LINKS = [
    {"rel": "icon", "href": "/favicon.ico", "sizes": "32x32"},
    {"rel": "icon", "type": "image/svg+xml", "href-begins": "data:image/svg+xml,"},
    {"rel": "apple-touch-icon", "href": "/apple-touch-icon.png"},
    {"rel": "manifest", "href": "/site.webmanifest"},
]


def test_T019_1_family_icon_links():
    """@prd T-019.1"""
    assert_icon_links(Page("family.html"), ICON_LINKS)


def test_T019_2_ivan_icon_links():
    """@prd T-019.2"""
    assert_icon_links(Page("ivan.html"), ICON_LINKS)


def test_T020_1_family_loads_nothing_remote():
    """@prd T-020.1"""
    page = Page("family.html")
    assert_loaded_references_local(page)
    assert_style_none_of(page, ["url(", "@import"])


def test_T020_2_ivan_loads_nothing_remote():
    """@prd T-020.2"""
    page = Page("ivan.html")
    assert_loaded_references_local(page)
    assert_style_none_of(page, ["url(", "@import"])


def test_T020_3_family_script_elements():
    """@prd T-020.3"""
    assert script_elements(Page("family.html")) == [{"type": "application/ld+json", "src": "none"}]


def test_T020_4_ivan_script_elements():
    """@prd T-020.4"""
    assert script_elements(Page("ivan.html")) == [{"type": "application/ld+json", "src": "none"}]


THEME_COLORS = [
    {"content": "#f5f1ea", "media": "(prefers-color-scheme: light)"},
    {"content": "#15130f", "media": "(prefers-color-scheme: dark)"},
]
SCHEME_STYLE = [
    ":root { --bg: #f5f1ea; --ink: #1c1a16;",
    "@media (prefers-color-scheme: dark) { :root { --bg: #15130f; --ink: #ece6da;",
]


def test_T021_1_family_colour_scheme():
    """@prd T-021.1"""
    page = Page("family.html")
    assert_meta(page, {"color-scheme": "light dark"})
    assert theme_colors(page) == THEME_COLORS
    assert_style_holds(page, SCHEME_STYLE)


def test_T021_2_ivan_colour_scheme():
    """@prd T-021.2"""
    page = Page("ivan.html")
    assert_meta(page, {"color-scheme": "light dark"})
    assert theme_colors(page) == THEME_COLORS
    assert_style_holds(page, SCHEME_STYLE)


ANIMATIONS = [
    "animation: drift-a 54s ease-in-out infinite alternate;",
    "animation: drift-b 73s ease-in-out infinite alternate, breathe 97s ease-in-out infinite alternate;",
]
REDUCED_MOTION = ["@media (prefers-reduced-motion: reduce) { body::before, body::after { animation: none; } body::after { opacity: 0.8; } }"]


def test_T022_1_family_animation():
    """@prd T-022.1"""
    assert_style_holds(Page("family.html"), ANIMATIONS)


def test_T022_2_ivan_animation():
    """@prd T-022.2"""
    assert_style_holds(Page("ivan.html"), ANIMATIONS)


def test_T022_3_family_reduced_motion():
    """@prd T-022.3"""
    assert_style_holds(Page("family.html"), REDUCED_MOTION)


def test_T022_4_ivan_reduced_motion():
    """@prd T-022.4"""
    assert_style_holds(Page("ivan.html"), REDUCED_MOTION)
