@echo off
cd /d %~dp0
set PYTHONPATH=%CD%
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000





