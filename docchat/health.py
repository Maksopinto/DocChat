"""Перевірка готовності: чого бракує, щоб програма працювала (особливо офлайн)."""

import os

from . import local_server, paths, settings
from .backend import LOCAL_BASE_URL


def check() -> list[dict]:
    """Список пунктів: {title, ok, required, hint}. required=False - необов'язкове."""
    items = []

    items.append({
        "title": "Модель пошуку по документах",
        "ok": paths.embedding_model_cached(),
        "required": True,
        "hint": "Потрібна одноразово. На ПК з інтернетом вона завантажується сама під час першого пошуку. "
                "Для ПК без інтернету підготуй її командою python tools/prepare_embedding_model.py "
                "і поклади папку models\\embedding поруч із програмою.",
    })

    external = local_server._responds(LOCAL_BASE_URL, timeout=0.5)
    exe, model = local_server.find_server_binary(), local_server.find_model()
    items.append({
        "title": "Локальна модель відповідей",
        "ok": external or model is not None,
        "required": False,
        "hint": "Файл .gguf поклади в папку models поруч із програмою. Без неї офлайн-режим не працюватиме.",
    })
    items.append({
        "title": "Локальний сервер (llama-server)",
        "ok": external or exe is not None,
        "required": False,
        "hint": "Файли llama.cpp мають лежати в папці bin\\llama поруч із програмою.",
    })

    has_key = bool(os.getenv("ANTHROPIC_API_KEY") or settings.get_api_key())
    items.append({
        "title": "Ключ Claude API",
        "ok": has_key,
        "required": False,
        "hint": "Потрібен лише для онлайн-режиму. Його вводять у «Налаштуваннях».",
    })
    return items


def can_answer() -> bool:
    """Чи є хоч якийсь спосіб відповісти: локальна модель з сервером або ключ."""
    by_title = {i["title"]: i["ok"] for i in check()}
    local = by_title["Локальна модель відповідей"] and by_title["Локальний сервер (llama-server)"]
    return bool(local or by_title["Ключ Claude API"])


def blocking_problems() -> list[dict]:
    """Що заважає працювати зараз: обов'язкове, що не готове, або відсутність будь-якого способу відповісти."""
    items = check()
    problems = [i for i in items if i["required"] and not i["ok"]]
    if not can_answer():
        problems += [i for i in items if not i["required"] and not i["ok"] and i["title"] != "Ключ Claude API"]
        problems += [i for i in items if i["title"] == "Ключ Claude API" and not i["ok"]]
    return problems
