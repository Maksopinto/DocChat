"""Вибір режиму роботи (онлайн / офлайн) і налаштування для кожного режиму.

Усі параметри можна змінити у файлі .env, змінюючи код не потрібно:

    DOCCHAT_MODE=auto          # auto | online | offline
    LOCAL_BASE_URL=http://localhost:1234/v1     # LM Studio. Для Ollama: http://localhost:11434/v1
    LOCAL_MODEL=               # порожньо = взяти першу завантажену модель
    ONLINE_TOP_K=8             # скільки шматків шукати в онлайні
    ONLINE_NEIGHBORS=1         # скільки сусідів додавати до кожного
    OFFLINE_TOP_K=3            # у офлайні контекст легший, бо локальна модель на CPU повільна
    OFFLINE_NEIGHBORS=0
"""

import os
import socket

from dotenv import load_dotenv

load_dotenv()

LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:1234/v1").rstrip("/")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "").strip()

PROFILES = {
    "online": {
        "top_k": int(os.getenv("ONLINE_TOP_K", "8")),
        "neighbors": int(os.getenv("ONLINE_NEIGHBORS", "1")),
    },
    "offline": {
        "top_k": int(os.getenv("OFFLINE_TOP_K", "3")),
        "neighbors": int(os.getenv("OFFLINE_NEIGHBORS", "0")),
    },
}

VALID_PREFERENCES = ("auto", "online", "offline")


class BackendUnavailable(RuntimeError):
    """Обраний бекенд (хмара чи локальний сервер) недоступний."""


def offline_only() -> bool:
    """Жорстка заборона виходу в інтернет (перемикач у налаштуваннях або DOCCHAT_OFFLINE_ONLY=1)."""
    return os.getenv("DOCCHAT_OFFLINE_ONLY", "").strip().lower() in ("1", "true", "yes")


def default_preference() -> str:
    value = os.getenv("DOCCHAT_MODE", "auto").strip().lower()
    return value if value in VALID_PREFERENCES else "auto"


def internet_available(host: str = "api.anthropic.com", port: int = 443, timeout: float = 2.0) -> bool:
    """Перевіряє, чи можна дістатися до API (проста спроба з'єднання)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def resolve_mode(preference: str = "auto") -> str:
    """auto -> 'online', якщо є ключ і зв'язок, інакше 'offline'."""
    if offline_only():
        return "offline"
    if preference in ("online", "offline"):
        return preference
    if os.getenv("ANTHROPIC_API_KEY") and internet_available():
        return "online"
    return "offline"
