@echo off
REM run_all_tests.bat — Délègue au runner Python multiplateforme
.venv\Scripts\python.exe run_all_tests.py
exit /b %ERRORLEVEL%
