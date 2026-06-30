"""SOP Studio utilities."""

from __future__ import annotations

import html
import re
from difflib import SequenceMatcher


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def plain_to_html(text: str) -> str:
    paragraphs = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    if not paragraphs:
        return "<p></p>"
    return "".join(f"<p>{html.escape(p)}</p>" for p in paragraphs)


def html_to_plain(content_html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", content_html or "", flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def text_similarity(a: str, b: str) -> float:
    return round(SequenceMatcher(None, a or "", b or "").ratio() * 100, 2)


def diff_summary(a: str, b: str) -> str:
    ratio = text_similarity(a, b)
    delta_words = count_words(b) - count_words(a)
    sign = "+" if delta_words >= 0 else ""
    return f"{ratio}% similar; {sign}{delta_words} words vs prior version."
