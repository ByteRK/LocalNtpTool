@echo off
setlocal
set "ROOT_DIR=%~dp0"

if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
  echo Using project virtual environment: %ROOT_DIR%\.venv\Scripts\python.exe
  "%ROOT_DIR%\.venv\Scripts\python.exe" "%ROOT_DIR%\run_ntp_tool.py" %*
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  echo Using system Python: python
  python "%ROOT_DIR%\run_ntp_tool.py" %*
  exit /b %errorlevel%
)

echo Python was not found. Create .venv or install Python first.
exit /b 1
