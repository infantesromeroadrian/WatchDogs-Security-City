"""
ReportLab-safe paragraphs.

``Paragraph`` parses an XML-like mini-language (``<img src=...>``, ``<font>``, ``<a>`` ...). Report text
includes model output derived from untrusted images, so it must not be able to inject markup (for
example ``<img src="file:///...">`` or ``<a href>``). Only the tags the report itself uses are kept; every
other ``<`` and ``&`` is escaped. If the surviving tags are unbalanced the text falls back to full escaping.
"""

import html
import re

from reportlab.platypus import Paragraph

_ALLOWED_TAG = re.compile(r"(</?(?:b|i)>|<br\s*/>)")


def safe_markup(text: object) -> str:
    """Escape everything except ``<b>``, ``<i>`` and ``<br/>``."""
    parts = _ALLOWED_TAG.split(str(text))
    return "".join(
        part if _ALLOWED_TAG.fullmatch(part) else html.escape(part, quote=False) for part in parts
    )


class SafeParagraph(Paragraph):
    """Paragraph that cannot be driven by markup inside model-generated text."""

    def __init__(self, text: object, *args, **kwargs):
        try:
            super().__init__(safe_markup(text), *args, **kwargs)
        except Exception:  # noqa: BLE001 - unbalanced allowed tags etc.: fall back to plain text
            super().__init__(html.escape(str(text), quote=False), *args, **kwargs)
