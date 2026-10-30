@echo off
setlocal
title Scrub OpenVanilla history
rem Removes Classic+'s old patch-Z.MPQ (whole game tables) and the old full-client download links from
rem EVERY commit and tag of github.com/orionopenwow/OpenVanilla, verifies the result, shows what it will
rem force-push, and pushes only after you type SCRUB. Details: scrub_history.py next to this file.
rem Before running: merge legal-cleanup-20261029 into main (and release it), so main's tree is already clean.
echo.
echo  Scrub OpenVanilla history
echo  -------------------------
where git >nul 2>nul || (echo Git is not installed. Install Git for Windows and run this again.& goto :end)
where py >nul 2>nul || (echo Python 3 is not installed ^(the "py" launcher^). Install it and run this again.& goto :end)
git filter-repo --version >nul 2>nul
if errorlevel 1 (
  py -3 -m git_filter_repo --version >nul 2>nul
  if errorlevel 1 (
    echo Installing git-filter-repo for this user...
    py -3 -m pip install --user --quiet git-filter-repo || (echo Could not install git-filter-repo.& goto :end)
  )
)
rem Commits and the push are Orion's, whatever this PC's global git identity is.
set GIT_AUTHOR_NAME=Orion
set GIT_AUTHOR_EMAIL=orionopenwow@users.noreply.github.com
set GIT_COMMITTER_NAME=Orion
set GIT_COMMITTER_EMAIL=orionopenwow@users.noreply.github.com
set WORK=%TEMP%\openvanilla-scrub-%RANDOM%
echo Working folder: %WORK%
echo.
py -3 "%~dp0scrub_history.py" --work "%WORK%"
echo.
echo  Remember: forks and anyone's existing clones keep the old history. GitHub may keep cached views of
echo  old commits and pull requests until GitHub Support runs a garbage collection: open a support request
echo  for orionopenwow/OpenVanilla and name the removed file (realm/classicplus/patch-Z.MPQ).
echo  You can delete %WORK% when you are done.
:end
echo.
pause
