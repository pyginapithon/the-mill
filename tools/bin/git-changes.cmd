@echo off
setlocal
set "REPO=%~dp0..\.."
python -m tools.git_changes %*
