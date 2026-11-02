"""Розрізання тексту на шматки (chunks) для пошуку.

Чому не можна просто віддати AI весь документ? Він може бути завеликий,
а нам потрібні лише ті фрагменти, що стосуються питання. Тому ріжемо текст
на невеликі шматки. Сусідні шматки трохи перекриваються (overlap), щоб
думка не обривалася рівно на межі.
"""

from dataclasses import dataclass

from .loader import Page


@dataclass
class Chunk:
    """Один шматок тексту з інформацією, звідки він узятий."""

    text: str
    source: str  # назва файлу
    page: int  # номер сторінки
    index: int  # порядковий номер шматка в документі


def split_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Ріже текст на шматки приблизно по chunk_size символів.

    Намагається різати по кінцю речення, а якщо його немає, то по пробілу,
    щоб не розривати слова.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap має бути меншим за chunk_size")

    text = " ".join(text.split())  # прибираємо зайві пробіли й переноси рядків
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            half = start + chunk_size // 2
            # шукаємо кінець речення в другій половині вікна
            sentence_end = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
            )
            if sentence_end > half:
                end = sentence_end + 1
            else:
                # якщо речення не знайшли, різати по пробілу
                space = text.rfind(" ", start, end)
                if space > half:
                    end = space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # наступний шматок починається трохи раніше кінця попереднього
        next_start = end - overlap
        space = text.find(" ", next_start, end)
        if space != -1:
            next_start = space + 1  # починаємо з цілого слова
        start = max(next_start, start + 1)  # гарантуємо, що рухаємось вперед

    return chunks


def chunk_pages(
    pages: list[Page],
    source: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[Chunk]:
    """Перетворює сторінки документа на список шматків.

    Кожна сторінка ріжеться окремо, тому в кожного шматка точний номер
    сторінки. Потім він піде в посилання на джерело у відповіді.
    """
    chunks: list[Chunk] = []
    for page in pages:
        for piece in split_text(page.text, chunk_size, overlap):
            chunks.append(
                Chunk(text=piece, source=source, page=page.number, index=len(chunks))
            )
    return chunks
