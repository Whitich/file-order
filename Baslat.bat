@echo off
cd /d "%~dp0"
python DosyaDuzeni.py
if errorlevel 1 pause
