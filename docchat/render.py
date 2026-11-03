"""Перетворення простого markdown у HTML для показу відповідей у вікні.

Підтримується те, що зазвичай пишуть моделі: заголовки, **жирний**, `код`,
маркований і нумерований списки. Увесь текст екранується, тому HTML зі
сторонніх документів у вікні не виконується.
"""

import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")
_BULLET = re.compile(r"^[-*•]\s+(.*)$")
_NUMBERED = re.compile(r"^\d+[.)]\s+(.*)$")


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = _BOLD.sub(r"<b>\1</b>", text)
    return _CODE.sub(r"<code>\1</code>", text)


def markdown_to_html(text: str) -> str:
    out: list[str] = []
    open_list: str | None = None  # "ul" або "ol"

    def close_list():
        nonlocal open_list
        if open_list:
            out.append(f"</{open_list}>")
            open_list = None

    def start_list(kind: str):
        nonlocal open_list
        if open_list != kind:
            close_list()
            out.append(f"<{kind}>")
            open_list = kind

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            close_list()
            continue

        if m := _HEADING.match(line):
            close_list()
            out.append(f"<p><b>{_inline(m.group(1))}</b></p>")
        elif m := _BULLET.match(line):
            start_list("ul")
            out.append(f"<li>{_inline(m.group(1))}</li>")
        elif m := _NUMBERED.match(line):
            start_list("ol")
            out.append(f"<li>{_inline(m.group(1))}</li>")
        else:
            close_list()
            out.append(f"<p>{_inline(line)}</p>")

    close_list()
    return "".join(out)
