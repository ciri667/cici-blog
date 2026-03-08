@echo off
setlocal

cd /d "%~dp0.."

echo Applying database migrations...
uv run alembic upgrade head
if errorlevel 1 exit /b %errorlevel%

echo Migration completed.

endlocal
