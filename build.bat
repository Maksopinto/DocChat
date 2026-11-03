@echo off
REM Build DocChat into dist\DocChat. Run with the project venv (.venv) activated.
REM This file must stay ASCII-only: cmd.exe misreads non-ASCII text in batch files.
setlocal
python -m pip install pyinstaller
if errorlevel 1 goto :fail

python -m PyInstaller DocChat.spec --noconfirm --clean
if errorlevel 1 goto :fail

REM Heavy files (llama server, models) are not bundled; they are copied next to DocChat.exe.
if exist bin\llama robocopy bin\llama dist\DocChat\bin\llama /E /NFL /NDL /NJH /NJS >nul
if exist models robocopy models dist\DocChat\models /E /NFL /NDL /NJH /NJS >nul

echo.
echo Done: dist\DocChat\DocChat.exe
exit /b 0

:fail
echo.
echo Build failed. Copy the error text above and send it to the assistant.
exit /b 1
