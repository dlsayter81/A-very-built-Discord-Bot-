@echo off
REM Create a new virtual environment and install dependencies

REM Step 1: Create a new virtual environment named 'env'
python -m venv env

REM Step 2: Activate the virtual environment
call env\Scripts\activate.bat

REM Step 3: Install dependencies from requirements.txt
pip install -r requirements.txt

echo Environment created and dependencies installed.
pause
