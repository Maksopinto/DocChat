"""Локальний сервер моделі: DocChat сам запускає llama-server, якщо інший сервер не знайдено.

Порядок:
 1. Якщо вже працює сервер за адресою LOCAL_BASE_URL (LM Studio, Ollama) - користуємось ним.
 2. Інакше шукаємо llama-server і файл моделі (.gguf) поруч із програмою й запускаємо у фоні.
 3. При виході з програми сервер зупиняється.

Налаштування (необов'язкові, змінні середовища або .env):
    LLAMA_SERVER_PATH   шлях до llama-server(.exe)
    LOCAL_MODEL_PATH    шлях до файлу моделі .gguf
    LOCAL_CTX           розмір контексту (за замовчуванням 8192)
"""

import atexit
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .backend import LOCAL_BASE_URL, BackendUnavailable
from .paths import app_dir, data_dir

LOG_DIR = data_dir()
START_TIMEOUT = 240  # секунд: завантаження моделі на слабкому ПК може тривати довго


def find_server_binary() -> Path | None:
    name = "llama-server.exe" if sys.platform == "win32" else "llama-server"
    candidates = []
    if os.getenv("LLAMA_SERVER_PATH"):
        candidates.append(Path(os.environ["LLAMA_SERVER_PATH"]))
    root = app_dir()
    candidates += [root / "bin" / "llama" / name, root / "llama" / name]
    for path in candidates:
        if path.is_file():
            return path
    found = shutil.which(name)
    return Path(found) if found else None


def find_model() -> Path | None:
    """Шукає файл моделі .gguf: спершу у вказаному шляху, потім поруч із програмою, потім у LM Studio."""
    if os.getenv("LOCAL_MODEL_PATH"):
        path = Path(os.environ["LOCAL_MODEL_PATH"])
        return path if path.is_file() else None
    for root in (app_dir() / "models", Path.home() / ".lmstudio" / "models"):
        if root.is_dir():
            # файли mmproj - допоміжні (для зображень), це не основна модель
            models = sorted(p for p in root.rglob("*.gguf") if not p.name.lower().startswith("mmproj"))
            if models:
                return models[0]
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _responds(base_url: str, timeout: float = 2.0) -> bool:
    """Сервер готовий, якщо /models віддає 200 (під час завантаження моделі він повертає 503)."""
    try:
        with urllib.request.urlopen(f"{base_url}/models", timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


class LocalServer:
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.base_url: str | None = None
        self._log_file = None
        atexit.register(self.stop)

    def ensure_running(self, on_status=None) -> str:
        """Повертає адресу готового сервера, за потреби запускаючи свій."""
        if _responds(LOCAL_BASE_URL):
            return LOCAL_BASE_URL
        if self.process and self.process.poll() is None and self.base_url and _responds(self.base_url):
            return self.base_url
        self.stop()  # попередній процес завершився або завис

        exe, model = find_server_binary(), find_model()
        if not exe:
            raise BackendUnavailable(
                "Не знайдено llama-server. Поклади його в папку bin\\llama поруч із програмою "
                "або запусти LM Studio / Ollama."
            )
        if not model:
            raise BackendUnavailable(
                "Не знайдено файл моделі (.gguf). Поклади його в папку models поруч із програмою "
                "або вкажи шлях у змінній LOCAL_MODEL_PATH."
            )

        port = _free_port()
        ctx = os.getenv("LOCAL_CTX", "8192")
        cmd = [
            str(exe), "-m", str(model),
            "--host", "127.0.0.1", "--port", str(port),
            "-c", ctx,
            "-np", "1",   # один паралельний запит, щоб увесь контекст діставався йому
            # без прихованих «роздумів» моделі: інакше перед першим словом 15-20 с тиші
            "--reasoning", "off",
        ]
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / "llama-server.log"
        self._log_file = open(log_path, "wb")
        if on_status:
            on_status(f"Запускаю локальну модель {model.name}...")
        self.process = subprocess.Popen(
            cmd,
            cwd=str(exe.parent),
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # без чорного вікна в Windows
        )
        self.base_url = f"http://127.0.0.1:{port}/v1"

        started = time.time()
        last_report = 0.0
        while time.time() - started < START_TIMEOUT:
            if self.process.poll() is not None:
                tail = self._log_tail(log_path)
                self.stop()
                raise BackendUnavailable(f"llama-server завершився одразу після запуску.\n{tail}")
            if _responds(self.base_url):
                return self.base_url
            elapsed = time.time() - started
            if on_status and elapsed - last_report >= 5:
                on_status(f"Завантажую модель у пам'ять... {int(elapsed)} с")
                last_report = elapsed
            time.sleep(0.5)

        self.stop()
        raise BackendUnavailable(
            f"Локальна модель не запустилась за {START_TIMEOUT} с. Деталі в журналі: {log_path}"
        )

    @staticmethod
    def _log_tail(path: Path, lines: int = 8) -> str:
        try:
            return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
        except OSError:
            return ""

    def stop(self):
        process, self.process = self.process, None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if self._log_file:
            self._log_file.close()
            self._log_file = None
        self.base_url = None


def diagnostics() -> dict:
    """Службова інформація для вікна налаштувань."""
    exe, model = find_server_binary(), find_model()
    return {
        "server": str(exe) if exe else None,
        "model": str(model) if model else None,
        "log_dir": str(LOG_DIR),
        "running": bool(_server.process and _server.process.poll() is None),
    }


_server = LocalServer()


def ensure_running(on_status=None) -> str:
    return _server.ensure_running(on_status)


def stop() -> None:
    _server.stop()
