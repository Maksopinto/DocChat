"""Завантаження документів: PDF, DOCX, TXT -> список сторінок з текстом."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Page:
    """Одна "сторінка" документа. Для txt/docx вважаємо весь файл однією сторінкою."""
    source: str   # назва файлу, потрібна щоб показувати джерело відповіді
    number: int   # номер сторінки (з 1)
    text: str


def clean_pdf_text(text: str) -> str:
    """Склеює слова, розірвані дефісом наприкінці рядка: 'відпо-\\nвідальність' -> 'відповідальність'.

    Чіпаємо лише дефіс, що впритул стоїть до літери, і після якого рядок
    продовжується малою літерою. Тире з пробілами (' - ') не чіпаємо.
    """
    return re.sub(r"(?<=\w)-\n\s*(?=[а-яіїєґa-z])", "", text)


def load_pdf(path: Path) -> list[Page]:
    from pypdf import PdfReader

    pages = []
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages, start=1):
        text = clean_pdf_text(page.extract_text() or "").strip()
        if text:  # порожні сторінки (скани без тексту) пропускаємо
            pages.append(Page(path.name, i, text))
    return pages


def load_docx(path: Path) -> list[Page]:
    from docx import Document

    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [Page(path.name, 1, text)] if text else []


def load_txt(path: Path) -> list[Page]:
    text = path.read_text(encoding="utf-8").strip()
    return [Page(path.name, 1, text)] if text else []


LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_txt,
}


def load_document(path: str | Path) -> list[Page]:
    path = Path(path)
    loader = LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Формат {path.suffix} не підтримується. Доступні: {', '.join(LOADERS)}")
    return loader(path)
