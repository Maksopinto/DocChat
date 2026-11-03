# -*- mode: python ; coding: utf-8 -*-
"""Конфіг збірки PyInstaller.

Збірка:  build.bat   (або: pyinstaller DocChat.spec --noconfirm)
Режим із чорним вікном консолі для пошуку помилок:  set DOCCHAT_CONSOLE=1  перед збіркою.
"""

import os

from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hiddenimports = [], [], []

# Пакети, які підвантажують модулі й дані динамічно: збираємо їх повністю.
for package in ("chromadb", "sentence_transformers", "tokenizers", "onnxruntime"):
    try:
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"[spec] пропускаю {package}: {e}")

# Деякі бібліотеки читають власну версію через importlib.metadata, тому потрібні метадані пакетів.
for package in (
    "chromadb", "sentence-transformers", "transformers", "tokenizers", "huggingface-hub",
    "safetensors", "tqdm", "regex", "requests", "packaging", "filelock", "numpy", "torch",
    "pypdf", "python-docx", "anthropic", "python-dotenv", "keyring", "PySide6",
):
    try:
        datas += copy_metadata(package)
    except Exception:
        pass

datas += [("assets/icon.png", "assets"), ("assets/icon.ico", "assets")]
hiddenimports += ["keyring.backends.Windows", "docchat.settings_dialog"]

console = os.environ.get("DOCCHAT_CONSOLE") == "1"

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "IPython", "notebook", "pytest", "matplotlib"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # режим onedir: швидший старт і менше підозр антивірусів, ніж один великий .exe
    name="DocChat",
    icon="assets/icon.ico",
    console=console,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="DocChat", upx=False)
