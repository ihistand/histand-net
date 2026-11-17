#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.2"]
# ///
"""Validator of the `hosting` contract type: the hosting rules of a static site.

Usage: validate_hosting.py <contract.yaml> [<contract.yaml> ...]

prd-toolkit lint runs it from the PRD folder with the type's files appended. It reads only those
files and the repository that holds them (the nearest folder above a contract file that has a
`.git`), so it names no site of its own. Exit 0 when every file is valid, 1 with one line per
defect on stderr, 2 on a usage error.

Shape: a YAML mapping (an empty one is valid) from a rule name to a mapping with

  rule     required  one of clean-urls, redirect, rewrite, not-deployed, crawl
  config   required  the repository file the rule is set in; it must exist, and a `.json` file
                     must parse as JSON

and, by rule:

  clean-urls    enabled      true or false: the site serves `/<name>` from `<name>.html`
  redirect      from-host    the host name requests arrive on (no scheme, no path); optional
                             when `from-path` is given, and then the rule holds on every host
                from-path    optional, the request path the rule is for, starting with `/`; with
                             no `from-path` the rule holds for every path
                to           the address they are sent to: an http(s) address, or a path
                             starting with `/` on the host the request arrived on
                permanent    true or false
                keeps-path   true or false: the request's path is kept on the new address
                A rule names `from-host`, `from-path` or both, and must not send a request to
                itself where that can be judged: a whole host to the same host, or a path to
                the same path on the same host.
  rewrite       path         the request path the rule is for, starting with `/`
                serves       the path served in its place, starting with `/`; when it names a
                             file (no `:`, `*`, `(`, `?` or `#` in it), the repository holds
                             `<serves>`, `<serves>.html` or `<serves>/index.html`
                host         optional, the host name the rule holds on (no scheme, no path); with
                             no `host` it holds on every host
  not-deployed  paths        a non-empty list of repository paths left out of the deploy; each
                             exists (a trailing `/` names a folder), unless it holds `*`, `?` or `[`
  crawl         user-agent   the crawler the rule is for (`*` for every crawler)
                allow        a non-empty list of paths, each starting with `/`
                disallow     optional, a list of paths, each starting with `/`
                sitemap      optional, the http(s) address of the sitemap; the config file
                             holds a line `Sitemap: <sitemap>`

Any other key is a defect.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml

NAME = re.compile(r"^[a-z][a-z0-9-]*$")
HOST = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")
RULES = {
    "clean-urls": {"enabled"},
    "redirect": {"to", "permanent", "keeps-path"},
    "rewrite": {"path", "serves"},
    "not-deployed": {"paths"},
    "crawl": {"user-agent", "allow"},
}
OPTIONAL = {"redirect": {"from-host", "from-path"}, "rewrite": {"host"}, "crawl": {"disallow", "sitemap"}}
NOT_A_FILE = re.compile(r"[:*(?#]")


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


def inside(root: Path, rel: str) -> Path | None:
    if not is_str(rel) or rel.startswith("/") or ".." in Path(rel).parts:
        return None
    return root / rel


def is_http(v) -> bool:
    parts = urlsplit(v) if is_str(v) else None
    return parts is not None and parts.scheme in ("http", "https") and bool(parts.netloc) and not re.search(r"\s", v)


def is_path(v) -> bool:
    return is_str(v) and v.startswith("/") and not v.startswith("//") and not re.search(r"\s", v)


def is_host(v) -> bool:
    return is_str(v) and bool(HOST.match(v))


def paths_list(v, *, empty_ok: bool) -> bool:
    return isinstance(v, list) and (empty_ok or bool(v)) and all(is_str(x) and x.startswith("/") for x in v)


def check_item(where: str, item: dict, root: Path) -> list[str]:
    bad: list[str] = []
    rule = item.get("rule")
    if rule not in RULES:
        return [f"{where}: rule must be one of {', '.join(sorted(RULES))}"]
    allowed = {"rule", "config"} | RULES[rule] | OPTIONAL.get(rule, set())
    for k in sorted(set(item) - allowed):
        bad.append(f"{where}: unknown key {k!r} for rule {rule}")
    for k in sorted(RULES[rule] - set(item)):
        bad.append(f"{where}: {k} is required for rule {rule}")

    cfg = item.get("config")
    p = inside(root, cfg) if is_str(cfg) else None
    if p is None or not p.is_file():
        bad.append(f"{where}: config {cfg!r} is not a file of the repository")
    elif p.suffix == ".json":
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            bad.append(f"{where}: config {cfg!r} is not valid JSON: {e}")

    if rule == "clean-urls" and "enabled" in item and not isinstance(item["enabled"], bool):
        bad.append(f"{where}: enabled must be true or false")
    if rule == "redirect":
        if "from-host" not in item and "from-path" not in item:
            bad.append(f"{where}: from-host or from-path is required for rule redirect")
        h = item.get("from-host")
        if "from-host" in item and not is_host(h):
            bad.append(f"{where}: from-host must be a host name, with no scheme or path")
        fp = item.get("from-path")
        if "from-path" in item and not is_path(fp):
            bad.append(f"{where}: from-path must be a path starting with /")
        to = item.get("to")
        if "to" in item:
            if not (is_http(to) or is_path(to)):
                bad.append(f"{where}: to must be an http(s) address or a path starting with /")
            else:
                parts = urlsplit(to)
                # The target's host: the address's own, or the request's when `to` is a path.
                to_host = parts.hostname if parts.netloc else (h.lower() if is_host(h) else None)
                same_host = is_host(h) and to_host == h.lower()
                if same_host and "from-path" not in item:
                    bad.append(f"{where}: to sends {h} to itself")
                elif is_path(fp) and (parts.path or "/") == fp and (same_host or not parts.netloc):
                    bad.append(f"{where}: to sends {fp} to itself")
        for k in ("permanent", "keeps-path"):
            if k in item and not isinstance(item[k], bool):
                bad.append(f"{where}: {k} must be true or false")
    if rule == "rewrite":
        for k in ("path", "serves"):
            if k in item and not is_path(item[k]):
                bad.append(f"{where}: {k} must be a path starting with /")
        if "host" in item and not is_host(item["host"]):
            bad.append(f"{where}: host must be a host name, with no scheme or path")
        dest = item.get("serves")
        if is_path(dest) and not NOT_A_FILE.search(dest):
            rel = dest.strip("/")
            names = [f"{rel}/index.html" if rel else "index.html"]
            if rel:
                names[:0] = [rel, f"{rel}.html"]
            if not any((q := inside(root, n)) is not None and q.is_file() for n in names):
                bad.append(f"{where}: serves {dest!r} names no file of the repository ({', '.join(names)})")
    if rule == "not-deployed" and "paths" in item:
        v = item["paths"]
        if not isinstance(v, list) or not v or not all(is_str(x) for x in v):
            bad.append(f"{where}: paths must be a non-empty list of repository paths")
        else:
            for rel in v:
                if any(c in rel for c in "*?["):
                    continue
                q = inside(root, rel.rstrip("/"))
                if q is None or not (q.is_dir() if rel.endswith("/") else q.exists()):
                    bad.append(f"{where}: path {rel!r} is not in the repository")
    if rule == "crawl":
        if "user-agent" in item and not is_str(item["user-agent"]):
            bad.append(f"{where}: user-agent must be a non-empty string")
        if "allow" in item and not paths_list(item["allow"], empty_ok=False):
            bad.append(f"{where}: allow must be a non-empty list of paths starting with /")
        if "disallow" in item and not paths_list(item["disallow"], empty_ok=True):
            bad.append(f"{where}: disallow must be a list of paths starting with /")
        sm = item.get("sitemap")
        if "sitemap" in item:
            if not is_http(sm):
                bad.append(f"{where}: sitemap must be an http(s) address")
            elif p is not None and p.is_file():
                try:
                    lines = p.read_text(encoding="utf-8").splitlines()
                except (OSError, ValueError) as e:
                    bad.append(f"{where}: config {cfg!r} does not read: {e}")
                else:
                    fields = (ln.partition(":") for ln in lines)
                    if not any(k.strip().lower() == "sitemap" and v.strip() == sm for k, _, v in fields):
                        bad.append(f"{where}: config {cfg!r} holds no line 'Sitemap: {sm}'")
    return bad


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_hosting.py <contract.yaml> [...]", file=sys.stderr)
        return 2
    bad: list[str] = []
    for arg in argv:
        path = Path(arg).resolve()
        root = repo_root(path)
        if root is None:
            bad.append(f"{arg}: not inside a git repository")
            continue
        try:
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        except (OSError, yaml.YAMLError) as e:
            bad.append(f"{arg}: does not load: {e}".replace("\n", " "))
            continue
        if data is None:
            data = {}
        if not isinstance(data, dict):
            bad.append(f"{arg}: top level must be a mapping from rule name to rule")
            continue
        for name, item in data.items():
            where = f"{arg}: {name}"
            if not isinstance(name, str) or not NAME.match(name):
                bad.append(f"{where}: rule name must match {NAME.pattern}")
            if not isinstance(item, dict):
                bad.append(f"{where}: must be a mapping")
                continue
            bad.extend(check_item(where, item, root))
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
