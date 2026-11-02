"""Читання документів. Поки що підтримуємо тільки PDF."""

from dataclasses import dataclass
from pathlib import Path

import fitz  # так імпортується бібліотека PyMuPDF


@dataclass
class Page:
    """Одна сторінка документа."""

    number: int  # номер сторінки (починаючи з 1)
    text: str  # текст сторінки


def load_pdf(path: str | Path) -> list[Page]:
    """Читає PDF і повертає список сторінок, на яких є текст.

    Сторінки без тексту (наприклад, скани-картинки) пропускаються.
    Для сканів потрібне розпізнавання тексту (OCR), це додамо пізніше.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не знайдено: {path}")

    pages: list[Page] = []
    with fitz.open(path) as doc:
        for number, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                pages.append(Page(number=number, text=text))
    return pages
