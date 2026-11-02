"""Розрізання тексту на шматки (chunks) з невеликим перекриттям."""

from dataclasses import dataclass

from .loader import Page


@dataclass
class Chunk:
    source: str   # з якого файлу
    page: int     # з якої сторінки
    text: str


def split_text(text: str, size: int = 1200, overlap: int = 250) -> list[str]:
    """Ріже текст на шматки приблизно по `size` символів.

    Перекриття (`overlap`) потрібне, щоб думка, яка опинилась на межі
    двох шматків, не загубилась. Ріжемо по межі речення або слова,
    а не посеред слова.
    """
    if overlap >= size:
        raise ValueError("overlap має бути меншим за size")

    text = " ".join(text.split())  # прибираємо зайві пробіли й переноси
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # шукаємо кінець речення в останній третині вікна
            window_start = start + size * 2 // 3
            cut = max(text.rfind(". ", window_start, end), text.rfind("? ", window_start, end),
                      text.rfind("! ", window_start, end))
            if cut != -1:
                end = cut + 1
            else:
                # інакше ріжемо по пробілу
                space = text.rfind(" ", window_start, end)
                if space != -1:
                    end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


MIN_CHUNK_CHARS = 50  # коротші шматки вважаємо сміттям


def chunk_pages(pages: list[Page], size: int = 1200, overlap: int = 250) -> list[Chunk]:
    chunks = []
    for page in pages:
        for piece in split_text(page.text, size, overlap):
            if len(piece) >= MIN_CHUNK_CHARS:
                chunks.append(Chunk(page.source, page.number, piece))
    return chunks
