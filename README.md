# DocChat

Десктопний чатбот, який відповідає на питання по твоїх документах (RAG).
Працює онлайн (Claude API) і офлайн (локальна модель).

## Статус

- [x] Етап 1: читання PDF і розрізання на шматки
- [ ] Етап 2: ембединги, векторна база, відповіді з джерелами
- [ ] Етап 3: перемикач моделей (Claude API / Ollama)
- [ ] Етап 4: десктопний інтерфейс (PySide6)
- [ ] Етап 5: перевірка якості, упаковка в .exe

## Встановлення (Windows, PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск етапу 1

```powershell
python step1_chunks.py шлях\до\файлу.pdf
python step1_chunks.py файл.pdf --size 600 --overlap 100 --show 5
```

Скрипт покаже, скільки сторінок і шматків вийшло, та перші шматки з номерами сторінок.

## Структура

```
DocChat/
  step1_chunks.py        # демо етапу 1
  requirements.txt
  src/docchat/
    loader.py            # читання PDF
    chunker.py           # розрізання на шматки
```
