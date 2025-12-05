# PowerShell script to start the FastAPI server
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
$env:PYTHONPATH = $PWD
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000





