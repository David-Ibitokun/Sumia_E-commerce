@echo off
REM Development server startup script
REM Usage: run_server.bat

cd /d "%~dp0"
call venv\Scripts\activate
python manage.py runserver
cmd