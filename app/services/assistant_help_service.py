"""Deterministic retrieval over a bounded, explicitly approved local manifest.

This is not a generative model. No repository crawling or private-data indexing.
The manifest path and clock are server dependencies, never tool arguments.
"""
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from app.services.assistant_contracts import bounded_text
from app.services.assistant_links import canonical_url

MANIFEST = Path(__file__).resolve().parents[1] / "content" / "assistant_help" / "manifest.json"
SOURCES = {"work_records": "main.profesional_trabajos"}
FIELDS = {"id", "title", "text", "version", "audience", "approved_by", "approved_at",
          "valid_from", "valid_until", "status", "source"}


class HelpUnavailable(ValueError):
    pass


def instant(value):
    if type(value) is not str:
        raise ValueError()
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError()
    return result.astimezone(timezone.utc)


def tokens(value):
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", normalized))


def search(query, role, limit=3, *, path=MANIFEST, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        # Bound the read itself, not just the parsed object.
        with Path(path).open("rb") as stream:
            raw = stream.read(131073)
        if len(raw) > 131072:
            raise ValueError()
        manifest = json.loads(raw)
        if (type(manifest) is not dict or set(manifest) != {"version", "articles"}
                or type(manifest["version"]) is not int or manifest["version"] != 1
                or type(manifest["articles"]) is not list or len(manifest["articles"]) > 50):
            raise ValueError()
        candidates = []
        seen = set()
        for article in manifest["articles"]:
            if type(article) is not dict:
                raise ValueError()
            if article.get("status") != "APPROVED":
                continue
            if set(article) != FIELDS:
                raise ValueError()
            for key, maximum in {"id": 80, "title": 160, "text": 8000, "version": 40,
                                 "approved_by": 120, "source": 40}.items():
                if type(article[key]) is not str or not 1 <= len(article[key].strip()) <= maximum:
                    raise ValueError()
            if article["id"] in seen or article["source"] not in SOURCES:
                raise ValueError()
            seen.add(article["id"])
            if (type(article["audience"]) is not list or not article["audience"]
                    or any(type(r) is not str or r not in ("CLIENTE", "PROFESIONAL", "SUPER_ADMIN")
                           for r in article["audience"])):
                raise ValueError()
            start, end = instant(article["valid_from"]), instant(article["valid_until"])
            approved = instant(article["approved_at"])
            if start >= end or approved > start:
                raise ValueError()
            if not start <= now < end or approved > now or role not in article["audience"]:
                continue
            score = len(tokens(query) & tokens(article["title"] + " " + article["text"]))
            if score:
                candidates.append((score, article))
        candidates.sort(key=lambda item: (-item[0], item[1]["id"]))
        return {"items": [{"id": a["id"], "title": a["title"],
                            "excerpt": bounded_text(a["text"], 800), "version": a["version"],
                            "source": a["source"],
                            "url": canonical_url(SOURCES[a["source"]])}
                           for _, a in candidates[:limit]], "corpus_version": manifest["version"]}
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        raise HelpUnavailable() from None
