@echo off
cd /d "%~dp0"
python file_order.py
if errorlevel 1 pause
