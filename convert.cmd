@echo off
rem Markdown Converter for Windows.
rem   Double-click to be asked for a file or folder, drag a file or folder onto
rem   this file, or run:  convert.cmd <file-or-folder> [options]   (see --help)
rem The first run sets up a private Python environment in .venv (Setup); later
rem runs reuse it. Conversion itself never uses the internet.
setlocal EnableExtensions DisableDelayedExpansion

set "HERE=%~dp0"
set "VENV=%HERE%.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"
set "STAMP=%VENV%\requirements.lock.installed"
set "BUNDLE=%HERE%offline-bundle\windows-x64"

rem Explorer (double-click or drag-and-drop) runs us as  cmd /c "...convert.cmd ..."
rem and closes the window when we finish, so pause first. A command typed at a
rem cmd prompt has no script name in CMDCMDLINE.
set "PAUSE_AT_END="
set "LAUNCH=%CMDCMDLINE:"=%"
call set "LAUNCH_WITHOUT_ME=%%LAUNCH:%~nx0=%%"
if /i not "%LAUNCH_WITHOUT_ME%"=="%LAUNCH%" set "PAUSE_AT_END=1"
if defined MARKDOWN_CONVERTER_NO_PAUSE set "PAUSE_AT_END="

if not exist "%VENV_PY%" goto setup
if not exist "%STAMP%" goto setup
fc /b "%HERE%requirements.lock" "%STAMP%" >nul 2>&1 || goto setup
goto run

:setup
call :find_python
if not defined PY goto no_python
echo Setting up the Markdown Converter (first run only, this can take a few minutes)...
if not exist "%VENV_PY%" %PY% -m venv "%VENV%" || goto setup_failed
if exist "%BUNDLE%\" goto install_from_bundle
"%VENV_PY%" -m pip install --disable-pip-version-check --quiet -r "%HERE%requirements.lock" || goto setup_failed
goto setup_done
:install_from_bundle
echo Installing from the Offline Bundle in "%BUNDLE%".
"%VENV_PY%" -m pip install --disable-pip-version-check --quiet --no-index --find-links "%BUNDLE%" -r "%HERE%requirements.lock" || goto setup_failed
:setup_done
copy /y "%HERE%requirements.lock" "%STAMP%" >nul
echo Setup complete.
echo.

:run
set "PYTHONPATH=%HERE%src"
"%VENV_PY%" -m markdown_converter %*
set "RC=%ERRORLEVEL%"
goto finish

:no_python
echo.
echo Python 3.12, 3.13 or 3.14 is needed but was not found.
echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH"
echo during installation, then run the Markdown Converter again.
set "RC=1"
goto finish

:setup_failed
echo.
echo Setup did not complete. Check the messages above. Without internet access,
echo copy an Offline Bundle to "%BUNDLE%" first (see README).
if exist "%STAMP%" del "%STAMP%"
set "RC=1"
goto finish

:finish
if defined PAUSE_AT_END (
    echo.
    pause
)
exit /b %RC%

rem Sets PY to a command that runs Python 3.12 to 3.14, preferring the one on PATH.
:find_python
set "PY="
for %%C in (python python3) do if not defined PY call :try_python %%C
for %%V in (3.14 3.13 3.12) do if not defined PY call :try_python py -%%V
exit /b 0

:try_python
%* -c "import sys; sys.exit(0 if (3, 12) <= sys.version_info[:2] < (3, 15) else 1)" >nul 2>&1 && set "PY=%*"
exit /b 0
