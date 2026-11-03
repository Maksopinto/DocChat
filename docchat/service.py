"""Логіка застосунку без інтерфейсу: додавання документів і відповіді на питання.

Кожна функція приймає останнім аргументом `emit` - функцію, якою вона повідомляє
про хід роботи (прогрес, токени відповіді). Вікно викликає ці функції у фоновому потоці.
Важкі бібліотеки (torch, chromadb) імпортуються всередині функцій, щоб вікно відкривалось швидко.
"""

from pathlib import Path


def list_documents(emit) -> list[str]:
    from .index import list_indexed_sources

    emit(("status", "Завантажую список документів і модель пошуку..."))
    return list_indexed_sources()


def add_document(path: str, emit) -> dict:
    from .chunker import chunk_pages
    from .index import index_chunks, is_indexed
    from .loader import load_document

    file = Path(path)
    if is_indexed(file.name):
        return {"name": file.name, "skipped": True, "chunks": 0}

    emit(("status", f"Читаю {file.name}..."))
    chunks = chunk_pages(load_document(file))
    if not chunks:
        raise ValueError("У файлі не знайдено тексту (можливо, це скан без розпізнаного тексту).")

    emit(("status", f"Індексую {len(chunks)} шматків..."))
    index_chunks(chunks, on_progress=lambda done, total: emit(("progress", done, total)))
    return {"name": file.name, "skipped": False, "chunks": len(chunks)}


def remove_documents(names: list[str], emit) -> list[str]:
    from .index import delete_source

    for name in names:
        emit(("status", f"Видаляю {name} з бази..."))
        delete_source(name)
    return names


def answer_question(question: str, preference: str, sources: list[str] | None, emit) -> dict:
    """Шукає шматки й питає модель. При проблемах із хмарою в режимі auto переходить на локальну."""
    from .answer import BackendUnavailable, ask
    from .backend import PROFILES, resolve_mode
    from .index import expand_with_neighbors, search

    mode = resolve_mode(preference)
    emit(("mode", mode))

    def run(current_mode: str):
        profile = PROFILES[current_mode]
        emit(("status", f"Шукаю в документах (режим {current_mode})..."))
        hits = search(question, k=profile["top_k"], sources=sources)
        blocks = expand_with_neighbors(hits, radius=profile["neighbors"])
        on_token = (lambda piece: emit(("token", piece))) if current_mode == "offline" else None
        if current_mode == "offline":
            from . import local_server

            local_server.ensure_running(on_status=lambda s: emit(("status", s)))
        emit(("status", "Модель відповідає..."))
        text, usage = ask(question, blocks, current_mode, on_token=on_token)
        return text, usage, blocks

    try:
        text, usage, blocks = run(mode)
    except BackendUnavailable as e:
        if preference == "auto" and mode == "online":
            mode = "offline"
            emit(("notice", f"{e}\nПеремикаюсь на локальну модель."))
            emit(("mode", mode))
            text, usage, blocks = run(mode)
        else:
            raise

    return {"mode": mode, "text": text, "usage": usage, "blocks": blocks, "streamed": mode == "offline"}
