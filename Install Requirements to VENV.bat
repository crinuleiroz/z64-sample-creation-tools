@ECHO OFF
:: Install "WAV to ZSOUND.py" requirements to a virtual environment

SET "VENV=.venv"

IF EXIST "%VENV%\Scripts\activate.bat" (
    ECHO Virtual environment already exists, skipping creation...
) ELSE (
		ECHO Creating virtual environment...
    py -m pip install --upgrade pip >NUL 2>&1
    py -m pip install virtualenv >NUL 2>&1
    py -m venv %VENV% >NUL 2>&1
)

:: Activate virtual environment and install the requirements
IF NOT EXIST "%VENV%\Scripts\activate.bat" (
		ECHO Failed to create virtual environment!
		PAUSE
    EXIT /B 1
) ELSE (
		CALL "%VENV%\Scripts\activate.bat"
		ECHO Installing "WAV to ZSOUND.py" requirements...
		py -m pip install --upgrade pip >NUL 2>&1
		py -m pip install -r requirements.txt >NUL 2>&1
)

:: Clear terminal and show success message
CLS
ECHO Virtual environment created and requirements installed successfully!
PAUSE