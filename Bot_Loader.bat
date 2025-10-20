@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Discord bot...
python Bot_Loader.py

pause
