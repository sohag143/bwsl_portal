@echo off
cd /d "%~dp0"
echo Starting BWSL Portal...
start "" "http://www.bwsl-portal.com:8000"
python manage.py runserver 0.0.0.0:8000
pause