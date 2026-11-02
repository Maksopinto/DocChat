"""Крок 1: читаємо документ і ріжемо його на шматки.

Запуск:  python step1_chunks.py шлях/до/файлу.pdf
"""

import sys

from docchat.chunker import chunk_pages
from docchat.loader import load_document


def main():
    if len(sys.argv) < 2:
        print("Використання: python step1_chunks.py <файл.pdf|docx|txt>")
        sys.exit(1)

    pages = load_document(sys.argv[1])
    chunks = chunk_pages(pages)

    print(f"Сторінок із текстом: {len(pages)}")
    print(f"Шматків: {len(chunks)}")
    if chunks:
        sizes = [len(c.text) for c in chunks]
        print(f"Розмір шматка: мін {min(sizes)}, макс {max(sizes)}, середній {sum(sizes) // len(sizes)} символів")

    print("\n--- Перші 3 шматки ---")
    for c in chunks[:3]:
        print(f"\n[{c.source}, стор. {c.page}]\n{c.text}")


if __name__ == "__main__":
    main()
