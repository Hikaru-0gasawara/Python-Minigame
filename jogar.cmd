@echo off
setlocal
rem Prefer the tested bundled runtime when available on this computer.
set "DUNGEON_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DUNGEON_PYTHON%" (
    "%DUNGEON_PYTHON%" "%~dp0dungeon_ui.py"
) else (
    python "%~dp0dungeon_ui.py"
)
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar. Use Python 3.10 ou superior com Tkinter.
    pause
)
