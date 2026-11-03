"""Налаштування користувача без файлу .env.

 - Звичайні значення (наприклад, перемикач «без інтернету») лежать у ~/.docchat/settings.json.
 - Ключ Claude API лежить у сховищі облікових даних Windows (бібліотека keyring),
   а не відкритим текстом. Якщо keyring недоступний, ключ живе лише до закриття програми.
 - apply_to_environment() передає збережене в змінні середовища, які вже читає решта коду.
   Значення з вікна налаштувань мають пріоритет над .env.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

SETTINGS_DIR = Path.home() / ".docchat"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
KEYRING_SERVICE = "DocChat"
KEYRING_USER = "anthropic_api_key"

_session_key = ""  # запасний варіант, коли keyring недоступний


def _keyring():
    try:
        import keyring
        return keyring
    except Exception:
        return None


def secure_storage_available() -> bool:
    return _keyring() is not None


# ---------- звичайні значення ----------

def load() -> dict:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(values: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")


def get_offline_only() -> bool:
    return bool(load().get("offline_only", False))


def set_offline_only(value: bool) -> None:
    values = load()
    values["offline_only"] = bool(value)
    save(values)


# ---------- ключ API ----------

def get_api_key() -> str:
    kr = _keyring()
    if kr:
        try:
            return kr.get_password(KEYRING_SERVICE, KEYRING_USER) or ""
        except Exception:
            pass
    return _session_key


def set_api_key(key: str) -> bool:
    """Зберігає ключ. Повертає True, якщо він збережений надовго (у сховищі Windows)."""
    global _session_key
    key = key.strip()
    kr = _keyring()
    if kr:
        try:
            if key:
                kr.set_password(KEYRING_SERVICE, KEYRING_USER, key)
            else:
                try:
                    kr.delete_password(KEYRING_SERVICE, KEYRING_USER)
                except Exception:
                    pass  # ключа й не було
            _session_key = ""
            return True
        except Exception:
            pass
    _session_key = key
    return False


# ---------- застосування ----------

def apply_to_environment() -> None:
    """Переносить збережені значення у змінні середовища (перекриваючи .env)."""
    key = get_api_key()
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key
    if get_offline_only():
        os.environ["DOCCHAT_OFFLINE_ONLY"] = "1"
    else:
        os.environ.pop("DOCCHAT_OFFLINE_ONLY", None)


def clear_api_key_from_environment() -> None:
    os.environ.pop("ANTHROPIC_API_KEY", None)


# ---------- перевірки ----------

def check_api_key(key: str, timeout: float = 8.0) -> tuple[bool, str]:
    """Перевіряє ключ запитом до списку моделей Claude (токени не витрачаються)."""
    key = key.strip()
    if not key:
        return False, "Ключ порожній."
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/models?limit=1",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            return True, "Ключ працює."
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, "Ключ не прийнято. Перевір, чи скопійовано його повністю."
        return False, f"Сервер відповів помилкою {e.code}."
    except (urllib.error.URLError, OSError):
        return False, "Немає зв'язку з Claude API (перевір інтернет)."
