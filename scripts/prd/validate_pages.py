#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.2"]
# ///
"""Validator of the `pages` contract type: which pages a static site serves and what each must hold.

Usage: validate_pages.py <contract.yaml> [<contract.yaml> ...]

prd-toolkit lint runs it from the PRD folder with the type's files appended. It reads only those
files and the repository that holds them (the nearest folder above a contract file that has a
`.git`), so it names no site of its own. Exit 0 when every file is valid, 1 with one line per
defect on stderr, 2 on a usage error.

Shape: a YAML mapping (an empty one is valid) from a page name to a mapping with

  url        required  the path the site serves the page at, starting with `/`
  host       optional  the host name the page is served on at `url` (no scheme, no path); pages
                       with no host share one default host
  file       required  the repository file served at `url`, an existing `.html` file
  title      required  the page's title text, non-empty
  canonical  required  the page's canonical address, http(s), whose path equals `url`, and
                       whose host equals `host` when the page has one
  source     optional  the repository file the page is generated from; it must exist
  generator  optional  the repository script that writes `file` from `source`; it must exist,
                       and `source` and `generator` are given together or not at all
  links      optional  hrefs the page links to; a local one (`/...`, not `//...`) must be the
                       `url` of a page on the same host in these files, or an existing
                       repository file
  holds      optional  plain-language statements of what the page must hold, non-empty strings

Across the files, each `file` belongs to one page, and each `url` to one page on each host. Any
other key is a defect.
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml

NAME = re.compile(r"^[a-z][a-z0-9-]*$")
HOST = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")
FIELDS = {"url", "host", "file", "title", "canonical", "source", "generator", "links", "holds"}
REQUIRED = ("url", "file", "title", "canonical")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _no_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"repeated key {key!r}", key_node.start_mark)
        seen.add(key)
    return loader.construct_mapping(node, deep)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def repo_root(path: Path) -> Path | None:
    for d in [path.parent, *path.parents]:
        if (d / ".git").exists():
            return d
    return None


def is_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def repo_file(root: Path, rel) -> bool:
    if not is_str(rel) or rel.startswith("/") or ".." in Path(rel).parts:
        return False
    return (root / rel).is_file()


def host_of(item: dict) -> str | None:
    h = item.get("host")
    return h.lower() if is_str(h) and HOST.match(h) else None


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_pages.py <contract.yaml> [...]", file=sys.stderr)
        return 2
    bad: list[str] = []
    pages: list[tuple[str, str, dict, Path]] = []  # (file label, name, item, repo root)
    for arg in argv:
        path = Path(arg).resolve()
        label = arg
        root = repo_root(path)
        if root is None:
            bad.append(f"{label}: not inside a git repository")
            continue
        try:
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        except (OSError, yaml.YAMLError) as e:
            bad.append(f"{label}: does not load: {e}".replace("\n", " "))
            continue
        if data is None:
            data = {}
        if not isinstance(data, dict):
            bad.append(f"{label}: top level must be a mapping from page name to page")
            continue
        for name, item in data.items():
            where = f"{label}: {name}"
            if not isinstance(name, str) or not NAME.match(name):
                bad.append(f"{where}: page name must match {NAME.pattern}")
            if not isinstance(item, dict):
                bad.append(f"{where}: must be a mapping")
                continue
            for k in sorted(set(item) - FIELDS):
                bad.append(f"{where}: unknown key {k!r}")
            for k in REQUIRED:
                if not is_str(item.get(k)):
                    bad.append(f"{where}: {k} is required and must be a non-empty string")
            url = item.get("url")
            if is_str(url) and not url.startswith("/"):
                bad.append(f"{where}: url must start with /")
            h = item.get("host")
            if "host" in item and not (is_str(h) and HOST.match(h)):
                bad.append(f"{where}: host must be a host name, with no scheme or path")
            f = item.get("file")
            if is_str(f):
                if not f.endswith(".html"):
                    bad.append(f"{where}: file must be an .html file")
                if not repo_file(root, f):
                    bad.append(f"{where}: file {f!r} is not a file of the repository")
            c = item.get("canonical")
            if is_str(c):
                parts = urlsplit(c)
                if parts.scheme not in ("http", "https") or not parts.netloc or re.search(r"\s", c):
                    bad.append(f"{where}: canonical must be an http(s) address")
                else:
                    if is_str(url) and (parts.path or "/") != url:
                        bad.append(f"{where}: canonical path {parts.path or '/'!r} is not the url {url!r}")
                    if host_of(item) is not None and parts.hostname != host_of(item):
                        bad.append(f"{where}: canonical host {parts.hostname!r} is not the host {h!r}")
            has_src, has_gen = "source" in item, "generator" in item
            if has_src != has_gen:
                bad.append(f"{where}: source and generator are given together or not at all")
            for k in ("source", "generator"):
                if k in item and not repo_file(root, item[k]):
                    bad.append(f"{where}: {k} {item[k]!r} is not a file of the repository")
            for k in ("links", "holds"):
                if k in item:
                    v = item[k]
                    if not isinstance(v, list) or not v or not all(is_str(x) for x in v):
                        bad.append(f"{where}: {k} must be a non-empty list of non-empty strings")
            pages.append((label, name, item, root))

    for k in ("url", "file"):
        owner: dict[tuple[str | None, str], str] = {}
        for label, name, item, _ in pages:
            v = item.get(k)
            if is_str(v):
                h = host_of(item) if k == "url" else None
                if (h, v) in owner:
                    on = f" on host {h}" if h is not None else ""
                    bad.append(f"{label}: {name}: {k} {v!r} is also page {owner[(h, v)]}'s{on}")
                else:
                    owner[(h, v)] = name

    urls = {(host_of(item), item["url"]) for _, _, item, _ in pages if is_str(item.get("url"))}
    for label, name, item, root in pages:
        links = item.get("links")
        if not isinstance(links, list):
            continue
        for href in links:
            if not is_str(href) or not href.startswith("/") or href.startswith("//"):
                continue
            target = re.split(r"[?#]", href, maxsplit=1)[0] or "/"
            if (host_of(item), target) in urls or repo_file(root, target.lstrip("/")):
                continue
            bad.append(f"{label}: {name}: link {href!r} is no page's url and no file of the repository")

    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
