@echo off
setlocal
cd /d "%~dp0"
title NebulaScope - GPU Monitor

call :prepare || goto :failed
start "" "http://127.0.0.1:8000"
echo.
echo NebulaScope is starting with real GPU metrics only...
echo Dashboard: http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" backend\main.py
goto :end

:prepare
if exist ".venv\Scripts\python.exe" goto :dependencies
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer first.
  exit /b 1
)
echo Creating the local Python environment...
python -m venv .venv || exit /b 1

:dependencies
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pynvml" >nul 2>nul
if not errorlevel 1 exit /b 0
echo Installing NebulaScope dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
exit /b 0

:failed
echo.
echo NebulaScope could not start. See the message above.
pause

:end
endlocal

