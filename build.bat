@echo off
REM Збірка DocChat у папку dist\DocChat. Запускати з активованим середовищем проєкту (.venv).
setlocal
python -m pip install pyinstaller
if errorlevel 1 goto :fail

python -m PyInstaller DocChat.spec --noconfirm --clean
if errorlevel 1 goto :fail

REM Важкі файли (сервер, моделі) не пакуємо в збірку, а кладемо поруч із DocChat.exe.
if exist bin\llama robocopy bin\llama dist\DocChat\bin\llama /E /NFL /NDL /NJH /NJS >nul
if exist models robocopy models dist\DocChat\models /E /NFL /NDL /NJH /NJS >nul

echo.
echo Готово: dist\DocChat\DocChat.exe
exit /b 0

:fail
echo.
echo Збірка не вдалась. Скопіюй текст помилки вище і надішли мені.
exit /b 1
