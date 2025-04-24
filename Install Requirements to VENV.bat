@echo off

set "VENV=.venv"

if not exist "%VENV%\Scripts\activate.bat" (
py -m pip install --upgrade pip
py -m pip install virtualenv
py -m venv %VENV%
)

if not exist "%VENV%\Scripts\activate.bat" exit /B 1

call "%VENV%\Scripts\activate.bat"
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

pause
exit /B 0