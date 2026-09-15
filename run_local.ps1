$ErrorActionPreference = "Stop"
if (-not (Test-Path "backend\.venv")) { python -m venv backend\.venv }
& backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:APEXGRID_RACE_MINUTES="2"
$env:APEXGRID_QUALIFYING_MINUTES="1"
$env:APEXGRID_PRACTICE_MINUTES="1"
$env:APEXGRID_ROUND_GAP_HOURS="0"
$env:APEXGRID_SEASON_GAP_HOURS="0"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD\backend'; & .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD\backend'; & .\.venv\Scripts\python.exe -m app.world_runner"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD'; python -m http.server 5500 --directory frontend"
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:5500"
