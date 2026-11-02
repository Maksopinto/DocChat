"""Крок 2: індексуємо документ і шукаємо по змісту (без AI-відповідей).

Запуск:  python step2_search.py samples/statuti_zsu.pdf

Спочатку документ індексується (один раз, може зайняти кілька хвилин),
потім можна вводити питання. Порожній рядок - вихід.
"""

import sys
import time
from pathlib import Path

from docchat.chunker import chunk_pages
from docchat.index import index_chunks, is_indexed, search
from docchat.loader import load_document


def main():
    if len(sys.argv) < 2:
        print("Використання: python step2_search.py <файл.pdf|docx|txt>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if is_indexed(path.name):
        print(f"{path.name} вже в базі, пропускаю індексацію.")
    else:
        chunks = chunk_pages(load_document(path))
        print(f"Індексую {len(chunks)} шматків ...")
        started = time.time()
        index_chunks(chunks)
        print(f"Готово за {time.time() - started:.0f} с.")

    print("\nВводь питання (порожній рядок - вихід).")
    while True:
        query = input("\nПитання: ").strip()
        if not query:
            break
        for i, hit in enumerate(search(query, k=5), start=1):
            print(f"\n#{i}  схожість {hit['score']:.2f}  [{hit['source']}, стор. {hit['page']}]")
            print(hit["text"][:400])


if __name__ == "__main__":
    main()
