"""Де програма шукає свої файли й де зберігає дані.

 - Папка програми (app_dir): там лежать bin/llama, models/ (поруч із .exe або в корені проєкту).
 - Папка даних (data_dir): база документів, налаштування, журнали. Вона в профілі користувача
   (C:\\Users\\<ім'я>\\.docchat), тому туди завжди можна писати, навіть коли програма стоїть
   у Program Files. Змінити можна змінною DOCCHAT_DATA_DIR.
"""

import os
import sys
from pathlib import Path

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
EMBEDDING_FOLDER = "multilingual-e5-small"


def app_dir() -> Path:
    """Папка програми: поруч із .exe у зібраній версії або корінь проєкту під час розробки."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(relative: str) -> Path:
    """Файл, вкладений у програму (іконка тощо): у зібраній версії лежить у службовій папці PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", app_dir()))
    return base / relative


def data_dir() -> Path:
    custom = os.getenv("DOCCHAT_DATA_DIR", "").strip()
    return Path(custom) if custom else Path.home() / ".docchat"


def db_dir() -> Path:
    """Папка бази документів. Стару базу з папки проєкту (db/) не втрачаємо: якщо нової ще немає, беремо її."""
    new = data_dir() / "db"
    legacy = app_dir() / "db"
    if not new.exists() and legacy.is_dir():
        return legacy
    return new


def local_embedding_dir() -> Path:
    return app_dir() / "models" / "embedding" / EMBEDDING_FOLDER


def embedding_model_source() -> str:
    """Шлях до вбудованої моделі пошуку, а якщо її немає, ім'я для завантаження з інтернету."""
    local = local_embedding_dir()
    return str(local) if (local / "config.json").is_file() else EMBEDDING_MODEL_NAME


def embedding_model_cached() -> bool:
    """Модель пошуку вже є на цьому ПК (поруч із програмою або в кеші HuggingFace)."""
    if embedding_model_source() != EMBEDDING_MODEL_NAME:
        return True
    hub = Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    return (hub / ("models--" + EMBEDDING_MODEL_NAME.replace("/", "--"))).is_dir()
