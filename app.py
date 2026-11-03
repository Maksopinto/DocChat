"""DocChat: графічний застосунок.

Запуск:  python app.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from docchat import service
from docchat.answer import NOT_FOUND
from docchat.backend import default_preference
from docchat.context import pages_label
from docchat.render import markdown_to_html

MODES = [
    ("auto", "Авто (Claude, якщо є інтернет)"),
    ("online", "Лише онлайн (Claude)"),
    ("offline", "Лише офлайн (локальна модель)"),
]


class Worker(QThread):
    """Виконує функцію у фоновому потоці, щоб вікно не зависало."""

    message = Signal(object)   # проміжні повідомлення (прогрес, токени)
    done = Signal(object)      # (вид задачі, результат)
    failed = Signal(object)    # (вид задачі, текст помилки)

    def __init__(self, kind: str, fn, *args):
        super().__init__()
        self.kind = kind
        self.fn = fn
        self.args = args

    def run(self):
        try:
            value = self.fn(*self.args, self.message.emit)
        except Exception as e:  # помилку показуємо у вікні, а не падаємо
            self.failed.emit((self.kind, f"{type(e).__name__}: {e}"))
        else:
            self.done.emit((self.kind, value))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocChat")
        self.resize(1000, 650)

        self._workers: list[Worker] = []
        self._index_queue: list[str] = []   # файли, що чекають на індексацію
        self._answer_started = False
        self._answer_start = 0              # позиція в чаті, з якої починається відповідь

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        self.setCentralWidget(splitter)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(220)
        self.progress.hide()
        self.statusBar().addPermanentWidget(self.progress)

        self._set_busy(True)
        self._start(Worker("docs", service.list_documents))

    # ---------- побудова інтерфейсу ----------
    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("Документи"))
        hint = QLabel("Якщо нічого не вибрано, пошук іде по всіх.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.doc_list = QListWidget()
        self.doc_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.doc_list)

        self.add_button = QPushButton("Додати документи...")
        self.add_button.clicked.connect(self.add_documents)
        layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Видалити вибрані")
        self.remove_button.clicked.connect(self.remove_documents)
        layout.addWidget(self.remove_button)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        top = QHBoxLayout()
        top.addWidget(QLabel("Режим:"))
        self.mode_combo = QComboBox()
        for value, title in MODES:
            self.mode_combo.addItem(title, value)
        index = self.mode_combo.findData(default_preference())
        self.mode_combo.setCurrentIndex(max(index, 0))
        top.addWidget(self.mode_combo)
        self.mode_label = QLabel("")
        top.addWidget(self.mode_label, stretch=1)
        layout.addLayout(top)

        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(False)
        layout.addWidget(self.chat)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Постав питання по документу...")
        self.input.returnPressed.connect(self.send_question)
        row.addWidget(self.input)

        self.send_button = QPushButton("Надіслати")
        self.send_button.clicked.connect(self.send_question)
        row.addWidget(self.send_button)
        layout.addLayout(row)
        return panel

    # ---------- фонові задачі ----------
    def _start(self, worker: Worker):
        # з'єднуємо з методами вікна: так Qt сам доставляє сигнали в головний потік
        worker.message.connect(self._on_message)
        worker.done.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(self._reap_workers)
        self._workers.append(worker)
        worker.start()

    def _reap_workers(self):
        for w in list(self._workers):
            if w.isFinished():
                w.wait()
                self._workers.remove(w)

    def _set_busy(self, busy: bool):
        for widget in (self.add_button, self.remove_button, self.send_button, self.input, self.mode_combo):
            widget.setEnabled(not busy)

    def _finish_task(self):
        self.progress.hide()
        self._set_busy(False)

    # ---------- реакції на події з потоків ----------
    def _on_message(self, payload):
        kind = payload[0]
        if kind == "status":
            self.statusBar().showMessage(payload[1])
        elif kind == "progress":
            done, total = payload[1], payload[2]
            self.progress.setMaximum(total)
            self.progress.setValue(done)
            self.progress.show()
            self.statusBar().showMessage(f"Індексація: {done} / {total}")
        elif kind == "mode":
            self.mode_label.setText(f"Режим відповіді: {payload[1]}")
        elif kind == "token":
            if not self._answer_started:
                self._start_answer()
            self._add_text(payload[1])
        elif kind == "notice":
            self.append_message("Система", payload[1])

    def _on_done(self, packed):
        kind, value = packed

        if kind == "index":
            self._on_index_done(value)
            if self._index_queue:          # у черзі ще є файли
                self._index_next()
                return

        self._finish_task()
        self.statusBar().showMessage("Готово", 4000)

        if kind == "docs":
            for name in value:
                self.doc_list.addItem(name)
            if value:
                self.append_message("Система", f"У базі {len(value)} документ(ів). Став питання.")
            else:
                self.append_message("Система", "База порожня. Додай документ кнопкою ліворуч.")
        elif kind == "remove":
            self._on_remove_done(value)
        elif kind == "answer":
            self._on_answer_done(value)

    def _on_failed(self, packed):
        kind, message = packed
        self.append_message("Помилка", message)
        if kind == "index" and self._index_queue:   # одна помилка не зупиняє решту файлів
            self._index_next()
            return
        self._finish_task()
        self.statusBar().clearMessage()

    # ---------- додавання документів ----------
    def add_documents(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Обери документи", "", "Документи (*.pdf *.docx *.txt)"
        )
        if not paths:
            return
        self._index_queue = list(paths)
        self._set_busy(True)
        self._index_next()

    def _index_next(self):
        path = self._index_queue.pop(0)
        self.statusBar().showMessage(f"Обробляю {Path(path).name}...")
        self._start(Worker("index", service.add_document, path))

    def _on_index_done(self, info: dict):
        name = info["name"]
        existing = [self.doc_list.item(i).text() for i in range(self.doc_list.count())]
        if name not in existing:
            self.doc_list.addItem(name)
        if info["skipped"]:
            self.append_message("Система", f"{name} уже є в базі.")
        else:
            self.append_message("Система", f"Додано {name}: {info['chunks']} шматків.")

    # ---------- видалення документів ----------
    def remove_documents(self):
        names = [item.text() for item in self.doc_list.selectedItems()]
        if not names:
            self.append_message("Система", "Спершу виділи в списку документи, які треба видалити.")
            return
        answer = QMessageBox.question(
            self,
            "Видалити з бази",
            "Видалити з бази DocChat:\n" + "\n".join(names) + "\n\nСамі файли на диску залишаться.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._set_busy(True)
        self._start(Worker("remove", service.remove_documents, names))

    def _on_remove_done(self, names: list):
        for name in names:
            for item in self.doc_list.findItems(name, Qt.MatchFlag.MatchExactly):
                self.doc_list.takeItem(self.doc_list.row(item))
        self.append_message("Система", "Видалено з бази: " + ", ".join(names))

    # ---------- питання й відповіді ----------
    def send_question(self):
        question = self.input.text().strip()
        if not question:
            return
        if self.doc_list.count() == 0:
            self.append_message("Система", "Спершу додай документ.")
            return

        self.input.clear()
        self.append_message("Ти", question)
        sources = [item.text() for item in self.doc_list.selectedItems()] or None
        preference = self.mode_combo.currentData()

        self._answer_started = False
        self._set_busy(True)
        self._start(Worker("answer", service.answer_question, question, preference, sources))

    def _on_answer_done(self, res: dict):
        if not self._answer_started:
            self._start_answer()
        self._finish_answer(res["text"])
        self.mode_label.setText(f"Режим відповіді: {res['mode']}")

        if NOT_FOUND not in res["text"]:
            lines = []
            for block in res["blocks"]:
                line = f"- {block['source']}, {pages_label(block)}"
                if res["mode"] == "offline":
                    line += f": {block['text'][:200]}..."
                lines.append(line)
            title = "Знайдені фрагменти" if res["mode"] == "offline" else "Джерела"
            self.append_message(title, "\n".join(lines))

        usage = res.get("usage") or {}
        if usage.get("input") is not None:
            self.statusBar().showMessage(
                f"Токени: вхід {usage.get('input')}, вихід {usage.get('output')}", 8000
            )

    # ---------- вивід у чат ----------
    def append_message(self, author: str, text: str):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self.chat.append(f"<p><b>{author}:</b><br>{safe}</p>")

    def _start_answer(self):
        """Починає блок відповіді: заголовок, далі текст дописується потоком."""
        self.chat.append("<p><b>DocChat:</b></p>")
        cursor = self.chat.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()
        self._answer_start = cursor.position()
        self.chat.setTextCursor(cursor)
        self._answer_started = True

    def _add_text(self, text: str):
        cursor = self.chat.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, QTextCharFormat())
        self.chat.setTextCursor(cursor)
        self.chat.ensureCursorVisible()

    def _finish_answer(self, text: str):
        """Замінює потоковий простий текст відповіді на відформатований (markdown -> HTML)."""
        cursor = self.chat.textCursor()
        cursor.setPosition(self._answer_start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        try:
            cursor.insertHtml(markdown_to_html(text))
        except Exception:
            cursor.insertText(text, QTextCharFormat())  # запасний варіант: простий текст
        self.chat.setTextCursor(cursor)
        self.chat.ensureCursorVisible()

    def closeEvent(self, event):
        for worker in self._workers:
            worker.wait(3000)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
