"""Вікно налаштувань: ключ Claude API, заборона інтернету, службова інформація."""

from PySide6.QtCore import QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from . import local_server, settings


class _KeyChecker(QThread):
    """Перевіряє ключ у фоні, щоб вікно не зависало, поки йде запит."""

    result = Signal(bool, str)

    def __init__(self, key: str):
        super().__init__()
        self.key = key

    def run(self):
        ok, text = settings.check_api_key(self.key)
        self.result.emit(ok, text)


def _section(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("section")
    return label


def _muted(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("muted")
    label.setWordWrap(True)
    return label


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Налаштування")
        self.setMinimumWidth(520)
        self._checker: _KeyChecker | None = None
        self._delete_key = False
        self._had_key = bool(settings.get_api_key())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)

        # --- ключ ---
        layout.addWidget(_section("КЛЮЧ CLAUDE API"))
        layout.addWidget(_muted(
            "Потрібен лише для онлайн-режиму. Без ключа програма працює з локальною моделлю."))
        row = QHBoxLayout()
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText(
            "Ключ збережено. Введи новий, щоб замінити" if self._had_key else "sk-ant-...")
        self.key_edit.textChanged.connect(self._on_key_typed)
        row.addWidget(self.key_edit, stretch=1)
        self.show_button = QPushButton("Показати")
        self.show_button.setCheckable(True)
        self.show_button.toggled.connect(self._toggle_show)
        row.addWidget(self.show_button)
        layout.addLayout(row)

        row = QHBoxLayout()
        self.check_button = QPushButton("Перевірити ключ")
        self.check_button.clicked.connect(self._check_key)
        row.addWidget(self.check_button)
        self.delete_button = QPushButton("Видалити ключ")
        self.delete_button.setEnabled(self._had_key)
        self.delete_button.clicked.connect(self._mark_delete)
        row.addWidget(self.delete_button)
        row.addStretch(1)
        layout.addLayout(row)
        self.key_status = _muted()
        layout.addWidget(self.key_status)
        if not settings.secure_storage_available():
            layout.addWidget(_muted(
                "Захищене сховище недоступне: ключ діятиме лише до закриття програми."))

        # --- приватність ---
        layout.addWidget(_section("ПРИВАТНІСТЬ"))
        self.offline_check = QCheckBox("Ніколи не виходити в інтернет (лише локальна модель)")
        self.offline_check.setChecked(settings.get_offline_only())
        layout.addWidget(self.offline_check)
        layout.addWidget(_muted(
            "Коли увімкнено, жоден документ чи питання не залишає цей комп'ютер, навіть якщо вказано ключ."))

        # --- службова інформація ---
        layout.addWidget(_section("СЛУЖБОВА ІНФОРМАЦІЯ"))
        info = local_server.diagnostics()
        layout.addWidget(_muted(f"Локальна модель: {info['model'] or 'не знайдено'}"))
        layout.addWidget(_muted(f"Локальний сервер: {info['server'] or 'не знайдено'}"))
        layout.addWidget(_muted(f"Журнали: {info['log_dir']}"))
        self._log_dir = info["log_dir"]
        log_button = QPushButton("Відкрити папку журналу")
        log_button.clicked.connect(self._open_logs)
        row = QHBoxLayout()
        row.addWidget(log_button)
        row.addStretch(1)
        layout.addLayout(row)

        # --- кнопки ---
        layout.addSpacing(6)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("Скасувати")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        save = QPushButton("Зберегти")
        save.setProperty("primary", True)
        save.setDefault(True)
        save.clicked.connect(self._save)
        row.addWidget(save)
        layout.addLayout(row)

    # ---------- дії ----------
    def _toggle_show(self, shown: bool):
        mode = QLineEdit.EchoMode.Normal if shown else QLineEdit.EchoMode.Password
        self.key_edit.setEchoMode(mode)
        self.show_button.setText("Сховати" if shown else "Показати")

    def _on_key_typed(self):
        if self.key_edit.text():
            self._delete_key = False

    def _mark_delete(self):
        self._delete_key = True
        self.key_edit.clear()
        self.key_status.setText("Ключ буде видалено після натискання «Зберегти».")

    def _check_key(self):
        key = self.key_edit.text().strip() or settings.get_api_key()
        if not key:
            self.key_status.setText("Спочатку введи ключ.")
            return
        self.check_button.setEnabled(False)
        self.key_status.setText("Перевіряю...")
        self._checker = _KeyChecker(key)
        self._checker.result.connect(self._on_checked)
        self._checker.start()

    def _on_checked(self, ok: bool, text: str):
        self.check_button.setEnabled(True)
        self.key_status.setText(text)

    def _open_logs(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self._log_dir))

    def _save(self):
        new_key = self.key_edit.text().strip()
        if self._delete_key:
            settings.set_api_key("")
            settings.clear_api_key_from_environment()
        elif new_key:
            settings.set_api_key(new_key)
        settings.set_offline_only(self.offline_check.isChecked())
        settings.apply_to_environment()
        self.accept()

    def done(self, code):
        # не закриваємо вікно, поки не завершилась перевірка ключа
        if self._checker is not None:
            self._checker.wait(10000)
        super().done(code)
