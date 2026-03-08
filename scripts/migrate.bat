@echo off
setlocal

cd /d "%~dp0.."

echo Checking whether database exists...
uv run python scripts/ensure_database.py
if errorlevel 1 exit /b %errorlevel%

echo Applying database migrations...
uv run alembic upgrade head
if errorlevel 1 exit /b %errorlevel%

echo Migration completed.

endlocal
