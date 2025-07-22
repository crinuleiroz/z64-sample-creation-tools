@ECHO OFF
:: Run "WAV to ZSOUND.py" — with drag-and-drop support — with its virtual environment

SET "SCRIPT_DIR=%~dp0"
SET "VENV=%SCRIPT_DIR%.venv"

:: Check for the virtual environment and activate it
IF EXIST "%VENV%\Scripts\activate.bat" (
    CALL "%VENV%\Scripts\activate.bat"
) ELSE (
    ECHO Virtual environment was not found, please run "Install Requirements to VENV.bat" before running this script.
    pause
    EXIT /B 1
)

:: Run "WAV to ZSOUND.py" in the virtual environment
python "%SCRIPT_DIR%WAV to ZSOUND.py" %*
