@echo off
setlocal

if "%~1"=="" (
    echo Usage: %~nx0 ^<migration_message^>
    echo Example: %~nx0 "initial_tables"
    exit /b 1
)

cd /d "%~dp0.."

echo Generating migration script: %~1
uv run alembic revision --autogenerate -m "%~1"
if errorlevel 1 exit /b %errorlevel%

echo Migration script generated. Please review the alembic\versions\ directory.
echo.
echo To apply migration, run: uv run alembic upgrade head

endlocal
