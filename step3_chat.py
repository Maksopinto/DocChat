"""Крок 3: питання по документу -> відповідь з посиланнями на сторінки.

Запуск:  python step3_chat.py samples/statuti_zsu.pdf

Режими (див. docchat/backend.py та файл .env):
  auto    - Claude, якщо є інтернет і ключ, інакше локальна модель (за замовчуванням)
  online  - завжди Claude
  offline - завжди локальна модель (LM Studio / Ollama)

Команди в чаті:  /auto  /online  /offline  /mode
Порожній рядок - вихід.
"""

import sys
import time
from pathlib import Path

from docchat.answer import CLAUDE_MODEL, BackendUnavailable, ask
from docchat.backend import LOCAL_BASE_URL, PROFILES, default_preference, resolve_mode
from docchat.chunker import chunk_pages
from docchat.context import pages_label
from docchat.index import expand_with_neighbors, index_chunks, is_indexed, search
from docchat.loader import load_document


def retrieve(question: str, mode: str) -> list[dict]:
    profile = PROFILES[mode]
    hits = search(question, k=profile["top_k"])
    return expand_with_neighbors(hits, radius=profile["neighbors"])


def answer_in_mode(question: str, mode: str) -> tuple[str, dict, list[dict]]:
    """Шукає шматки під профіль режиму й питає відповідну модель."""
    blocks = retrieve(question, mode)
    streamed = mode == "offline"
    if streamed:
        print()  # відповідь локальної моделі друкується по мірі генерації
    text, usage = ask(question, blocks, mode, on_token=(lambda t: print(t, end="", flush=True)) if streamed else None)
    if streamed:
        print()
    else:
        print(f"\n{text}")
    return text, usage, blocks


def main():
    if len(sys.argv) < 2:
        print("Використання: python step3_chat.py <файл.pdf|docx|txt>")
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

    preference = default_preference()
    print(f"\nРежим: {preference}. Команди: /auto /online /offline /mode")
    print(f"Онлайн: Claude ({CLAUDE_MODEL}). Офлайн: локальний сервер {LOCAL_BASE_URL}")
    print("Став питання (порожній рядок - вихід).")

    while True:
        question = input("\nПитання: ").strip()
        if not question:
            break

        if question in ("/auto", "/online", "/offline"):
            preference = question[1:]
            print(f"Режим змінено на {preference}.")
            continue
        if question == "/mode":
            print(f"Налаштування: {preference}. Зараз було б обрано: {resolve_mode(preference)}.")
            continue

        mode = resolve_mode(preference)
        print(f"[режим: {mode}]")
        try:
            try:
                text, usage, blocks = answer_in_mode(question, mode)
            except BackendUnavailable as e:
                # в автоматичному режимі при проблемах із хмарою пробуємо локальну модель
                if preference == "auto" and mode == "online":
                    print(f"\n{e}\nПеремикаюсь на локальну модель.\n[режим: offline]")
                    mode = "offline"
                    text, usage, blocks = answer_in_mode(question, mode)
                else:
                    raise
        except BackendUnavailable as e:
            print(f"\n{e}")
            continue

        if mode == "offline":
            # локальна модель може помилитись, тому показуємо справжній текст знайдених фрагментів
            print("\nЗнайдені фрагменти (початок):")
            for b in blocks:
                print(f"  - {b['source']}, {pages_label(b)}: {b['text'][:300]}...")
        else:
            print("\nДжерела, які бачив Claude:")
            for b in blocks:
                print(f"  - {b['source']}, {pages_label(b)}")

        if usage.get("input") is not None:
            print(f"Токени: вхід {usage.get('input')}, вихід {usage.get('output')}")


if __name__ == "__main__":
    main()
