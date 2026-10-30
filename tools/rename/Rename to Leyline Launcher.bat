@echo off
setlocal
title Rename the GitHub repo to Leyline-Launcher
rem Renames github.com/orionopenwow/OpenVanilla to github.com/orionopenwow/Leyline-Launcher with this PC's
rem GitHub CLI sign-in (orionopenwow only; it refuses Chumpton), sets the repo's description and homepage,
rem and points this folder's "origin" at the new address. Safe to run again: done steps are skipped.
rem GitHub redirects the old address, so old links, clones and the launcher's update downloads keep working.
rem   "Rename to Leyline Launcher.bat" dry    only says what it would do
rem Details: leyline_rename.py next to this file.
set GIT_TERMINAL_PROMPT=0
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (echo Python 3 is needed: https://www.python.org/downloads/ & goto :fail)
where git >nul 2>&1 || (echo Git is not installed: https://git-scm.com/download/win & goto :fail)
where gh >nul 2>&1 || (echo The GitHub CLI is not installed: winget install GitHub.cli  ^(then: gh auth login^) & goto :fail)
set "ARGS="
if /i "%~1"=="dry" set "ARGS=--dry-run"
%PY% "%~dp0leyline_rename.py" --clone "%~dp0..\.." %ARGS% || goto :fail
echo.
pause
exit /b 0
:fail
echo.
echo Nothing more was changed. Send Claude a screenshot of this window.
pause
exit /b 1
