#!/usr/bin/env python3
"""Offline, secret-free-key publication guard prototype. Never logs matching values."""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

MAX_FILES = 3000
MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 25_000_000
VALID_SHA = re.compile(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\Z")
TEXT_EXT = {".md", ".markdown", ".json", ".yaml", ".yml", ".html", ".xml", ".txt", ".csv"}
FILE_SCOPE = ("_articles/", "_columns/", "_data/", "docs/")


class Denied(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30, check=False,
    )
    if result.returncode:
        raise Denied()
    return result.stdout


def normalize(value):
    out = value
    for _ in range(3):
        decoded = unquote(out)
        if decoded == out:
            break
        out = decoded
    return unicodedata.normalize("NFKC", out).casefold()


def load_policy(path):
    try:
        raw = Path(path).read_bytes()
        if not raw or len(raw) > 256_000:
            raise Denied()
        cfg = json.loads(raw.decode("utf-8"))
        if not isinstance(cfg, dict) or set(cfg) != {"ids", "tickers", "names"}:
            raise Denied()
        for key in ("ids", "tickers", "names"):
            if not isinstance(cfg[key], list) or not cfg[key]:
                raise Denied()
            if any(not isinstance(x, str) or len(x.strip()) < (3 if key == "names" else 1)
                   or len(x) > 100 for x in cfg[key]):
                raise Denied()
        return {k: set(normalize(v) for v in cfg[k]) for k in cfg}
    except (OSError, UnicodeError, ValueError, TypeError):
        raise Denied() from None


def forbidden(value, field, policy):
    s = normalize(value)
    if field == "id":
        return s in policy["ids"]
    if field == "ticker":
        return s in policy["tickers"]
    if any(name in s for name in policy["names"]):
        return True
    # Standalone numeric tokens in free text are not proof of a ticker.
    # Require a nearby securities label to avoid timestamps and prices.
    for ticker in policy["tickers"]:
        if not ticker.isdigit():
            continue
        expr = r"(?<![0-9])" + re.escape(ticker) + r"(?![0-9])"
        for match in re.finditer(expr, s):
            context = s[max(0, match.start()-28):min(len(s), match.end()+28)]
            if any(label in context for label in ("ticker", "証券コード", "銘柄コード")):
                return True
    return False


def walk_structured(obj, policy):
    if isinstance(obj, dict):
        for key, value in obj.items():
            field = "id" if key in ("company_id", "id") else ("ticker" if key == "ticker" else "text")
            if isinstance(value, str) and forbidden(value, field, policy):
                raise Denied()
            walk_structured(value, policy)
    elif isinstance(obj, list):
        for item in obj:
            walk_structured(item, policy)


def scan(repo, sha, policy):
    if not VALID_SHA.fullmatch(sha):
        raise Denied()
    actual = git(repo, "rev-parse", "--verify", sha + "^{commit}").decode("ascii").strip()
    if actual.lower() != sha.lower():
        raise Denied()
    tree = git(repo, "ls-tree", "-rz", "--full-tree", sha)
    total = 0
    entries = tree.split(b"\0")
    if len(entries) > MAX_FILES + 1:
        raise Denied()
    for entry in entries:
        if not entry:
            continue
        try:
            meta, raw_path = entry.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split()
            path = raw_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError):
            raise Denied() from None
        parts = path.split("/")
        if any(p in ("", ".", "..") or p.endswith((" ", ".")) or
               p.upper().split(".")[0] in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}
               for p in parts):
            raise Denied()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise Denied()  # symlink, gitlink and unexpected object types
        normalized_path = normalize(path)
        if forbidden(normalized_path, "text", policy):
            raise Denied()
        if not path.startswith(FILE_SCOPE) and path not in ("README.md",):
            continue
        if Path(path).suffix.lower() not in TEXT_EXT:
            continue  # binaries are handled by a separate unprivileged review
        size = int(git(repo, "cat-file", "-s", oid))
        total += size
        if size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise Denied()
        data = git(repo, "cat-file", "blob", oid)
        try:
            body = data.decode("utf-8")
        except UnicodeError:
            raise Denied() from None
        if forbidden(body, "text", policy):
            raise Denied()
        if path.endswith(".json"):
            try:
                walk_structured(json.loads(body), policy)
            except (ValueError, TypeError):
                raise Denied() from None


def main():
    parser = argparse.ArgumentParser(description="Offline policy gate; no matching values printed")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--policy", required=True, help="Path outside the repository; never commit")
    args = parser.parse_args()
    try:
        policy = load_policy(args.policy)
        scan(Path(args.repo), args.sha, policy)
    except (Denied, OSError, subprocess.TimeoutExpired, OverflowError, RecursionError):
        print("FAIL: publication policy validation did not pass", file=sys.stderr)
        return 1
    print("PASS: publication policy validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
