"""Smoke tests for area `site` on production (docs/prd/histand-net/test-cases/site.yaml).

Every expected value is copied from the PRD's test cases; how a request is
sent and a response read is testing.md's Harness, "HTTP requests". Only GET
and HEAD are sent; redirects are not followed; each request times out after
30 s (Harness, "Waits").
"""

import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # tests/smoke/<file> -> the repository root

# A known-failing case (testing-from-prds): the test raises pytest's own
# expected-failure exception only when it sees the case's `symptom:`; the
# strict marker accepts only that exception, so any other failure fails.
KNOWN_FAILURE = pytest.xfail.Exception
TIMEOUT = 30
USER_AGENT = "prd-smoke"
_ASCII_WS = re.compile(r"[ \t\n\f\r]+")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # urllib then raises HTTPError carrying the 3xx response


_OPENER = urllib.request.build_opener(_NoRedirect)


class Response:
    def __init__(self, status, headers, body):
        self.status = status
        self._headers = headers
        self.body = body

    def header(self, name):
        """Looked up by name in any letter case; the value exactly as sent."""
        return self._headers.get(name)

    def text(self):
        return self.body.decode("utf-8")

    def title(self):
        return _first_title(self.text())

    def json(self):
        return json.loads(self.text())


def send(method, url):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with _OPENER.open(req, timeout=TIMEOUT) as r:
            return Response(r.status, r.headers, r.read())
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp is not None else b""
        return Response(e.code, e.headers, body)


def request(line):
    """A case's `request`: the method, a space and the URL."""
    method, url = line.split(" ", 1)
    return send(method, url)


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts = []
        self.done = False

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if tag == "title":
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self.depth and not self.done:
            self.depth -= 1
            if self.depth == 0:
                self.done = True

    def handle_data(self, data):
        if self.depth and not self.done:
            self.parts.append(data)


def _first_title(html):
    p = _TitleParser()
    p.feed(html)
    p.close()
    if not p.parts and not p.done:
        return None
    return _ASCII_WS.sub(" ", "".join(p.parts)).strip(" ")


def strict_eq(a, b):
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


def assert_redirect(r, location):
    assert (r.status, r.header("Location")) == (308, location)


def check_each(method, urls, status, location=None):
    wrong = []
    for url in urls:
        r = send(method, url)
        got = (r.status, r.header("Location")) if location is not None else r.status
        want = (status, location) if location is not None else status
        if got != want:
            wrong.append(f"{url}: {got!r}")
    return wrong


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_T001_1_family_page_at_root():
    """@prd T-001.1"""
    r = request("GET https://histand.net/")
    assert r.status == 200
    assert r.header("Content-Type") == "text/html; charset=utf-8"
    assert r.title() == "Histand — a family name in Doylestown, Bucks County"


def test_T002_1_name_card_at_root():
    """@prd T-002.1"""
    r = request("GET https://ivan.histand.net/")
    assert r.status == 200
    assert r.header("Content-Type") == "text/html; charset=utf-8"
    assert r.title() == "Ivan Histand"


def test_T003_1_family_html_to_clean_url():
    """@prd T-003.1"""
    assert_redirect(request("HEAD https://histand.net/family.html"), "/family")


def test_T004_1_family_to_root():
    """@prd T-004.1"""
    assert_redirect(request("HEAD https://histand.net/family"), "/")


def test_T004_3_family_to_root_on_ivan_host():
    """@prd T-004.3"""
    assert_redirect(request("HEAD https://ivan.histand.net/family"), "/")


def test_T005_1_ivan_to_subdomain():
    """@prd T-005.1"""
    assert_redirect(request("HEAD https://histand.net/ivan"), "https://ivan.histand.net/")


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason="E-001: /ivan on ivan.histand.net answers 200 instead of 308")
def test_T005_3_ivan_on_subdomain_to_root():
    """@prd T-005.3 known-failing E-001"""
    r = request("HEAD https://ivan.histand.net/ivan")
    got = (r.status, r.header("Location"))
    if got == (308, "https://ivan.histand.net/"):
        return
    if r.status == 200:
        pytest.xfail("E-001: /ivan on ivan.histand.net answers 200 instead of 308")
    raise AssertionError(f"not the known failure: {got!r}, expected (308, 'https://ivan.histand.net/')")


ALIAS_ROOTS = [
    "https://www.histand.net/", "https://histand.com/", "https://www.histand.com/",
    "https://histand.org/", "https://www.histand.org/", "https://histands.com/",
    "https://www.histands.com/", "https://histands.net/", "https://www.histands.net/",
    "https://histands.org/", "https://www.histands.org/", "https://anilak.net/",
    "https://www.anilak.net/", "https://hinault.net/", "https://www.hinault.net/",
    "https://ivanivan.net/", "https://www.ivanivan.net/",
]


def test_T006_1_alias_roots_to_apex():
    """@prd T-006.1"""
    wrong = check_each("HEAD", ALIAS_ROOTS, 308, "https://histand.net/")
    assert wrong == [], f"expected 308 to https://histand.net/: {wrong}"


def test_T006_2_alias_paths_kept():
    """@prd T-006.2"""
    expected = {
        "https://histand.com/robots.txt": "https://histand.net/robots.txt",
        "https://www.ivanivan.net/a/b": "https://histand.net/a/b",
        "https://www.histand.net/sitemap.xml": "https://histand.net/sitemap.xml",
        "https://www.ivanivan.net/a/b?x=1": "https://histand.net/a/b?x=1",
    }
    wrong = []
    for url, location in expected.items():
        r = send("HEAD", url)
        if (r.status, r.header("Location")) != (308, location):
            wrong.append(f"{url}: {(r.status, r.header('Location'))!r}, expected {(308, location)!r}")
    assert wrong == [], wrong


def test_T007_1_robots_txt():
    """@prd T-007.1"""
    r = request("GET https://histand.net/robots.txt")
    assert r.status == 200
    assert r.header("Content-Type") == "text/plain; charset=utf-8"
    assert r.text() == "User-agent: *\nAllow: /\n\nSitemap: https://histand.net/sitemap.xml\n"


def test_T008_2_sitemap_served():
    """@prd T-008.2"""
    r = request("GET https://histand.net/sitemap.xml")
    assert r.status == 200
    assert r.header("Content-Type") == "application/xml"
    assert r.body == (ROOT / "sitemap.xml").read_bytes()


def test_T009_2_manifest_served():
    """@prd T-009.2"""
    r = request("GET https://histand.net/site.webmanifest")
    assert r.status == 200
    assert r.header("Content-Type") == "application/manifest+json; charset=utf-8"
    expected = {
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
    actual = r.json()
    assert data_matches(expected, actual), f"manifest: {actual!r}"


@pytest.mark.xfail(strict=True, raises=KNOWN_FAILURE,
                   reason="E-006: one or more of the listed URLs answer 200 instead of 404")
def test_T010_2_non_site_files_not_served():
    """@prd T-010.2 known-failing E-006"""
    urls = [
        "https://histand.net/README.md",
        "https://histand.net/scripts/make-assets.py",
        "https://histand.net/scripts/fetch-icons.py",
        "https://histand.net/scripts/prd/validate_pages.py",
        "https://histand.net/docs/prd/histand-net/prd.md",
        "https://histand.net/tests/integration/test_site.py",
    ]
    statuses = {url: send("HEAD", url).status for url in urls}
    wrong = {url: s for url, s in statuses.items() if s != 404}
    if not wrong:
        return
    if all(s == 200 for s in wrong.values()):
        pytest.xfail(f"E-006: these URLs answer 200 instead of 404: {sorted(wrong)}")
    raise AssertionError(f"not the known failure: expected 404 from each, got {wrong}")


def test_T012_2_family_share_image():
    """@prd T-012.2"""
    r = request("HEAD https://histand.net/og-family.png")
    assert r.status == 200
    assert r.header("Content-Type") == "image/png"


def test_T016_2_ivan_share_image():
    """@prd T-016.2"""
    r = request("HEAD https://ivan.histand.net/og.png")
    assert r.status == 200
    assert r.header("Content-Type") == "image/png"


def test_T019_3_icons_and_manifest_served():
    """@prd T-019.3"""
    urls = [
        "https://histand.net/favicon.ico",
        "https://histand.net/apple-touch-icon.png",
        "https://histand.net/site.webmanifest",
        "https://ivan.histand.net/favicon.ico",
        "https://ivan.histand.net/apple-touch-icon.png",
        "https://ivan.histand.net/site.webmanifest",
    ]
    wrong = check_each("HEAD", urls, 200)
    assert wrong == [], f"expected 200: {wrong}"
