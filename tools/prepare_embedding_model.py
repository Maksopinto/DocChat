"""Готує модель пошуку для комп'ютерів без інтернету.

Запусти на ПК з інтернетом (у середовищі проєкту):
    python tools/prepare_embedding_model.py

Скрипт збереже модель у models/embedding/multilingual-e5-small.
Цю папку (models/embedding) потім копіюють поруч із програмою на ПК без інтернету.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentence_transformers import SentenceTransformer

from docchat.paths import EMBEDDING_MODEL_NAME, local_embedding_dir

target = local_embedding_dir()
print(f"Завантажую {EMBEDDING_MODEL_NAME} ...")
SentenceTransformer(EMBEDDING_MODEL_NAME).save(str(target))
print(f"Готово: {target}")
