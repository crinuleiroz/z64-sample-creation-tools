@echo off

:: Update PIP
python -m pip install --upgrade pip

:: Install from requirements.txt
python -m pip install -r requirements.txt

echo.
echo Requirements installation complete.
pause