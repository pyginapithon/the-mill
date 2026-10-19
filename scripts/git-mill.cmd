@echo off
REM Dogfood mill 0.3 from this git checkout. pip mill.exe 0.2.5 recreates v1 tables.
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "PYTHONPATH=%ROOT%"
set "PYTHONUNBUFFERED=1"
python -m agent_coord %*
