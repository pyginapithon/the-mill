@echo off
setlocal
set "REPO=%~dp0..\.."
set "PYTHONPATH=%REPO%"
python -m agent_coord.client.hold %*
