@echo off
REM =========================================
REM Activate venv and run S3 upload script
REM =========================================

set PROJECT_DIR=D:\Projects\OCR\lambdaFunctionOCR
set VENV_DIR=%PROJECT_DIR%\.venv
set SCRIPT=%PROJECT_DIR%\aws_s3_upload.py
set LOG_FILE=%PROJECT_DIR%\upload.log

REM --- Go to project directory ---
cd /d D:\Projects\OCR\lambdaFunctionOCR

REM --- Start logging ---
echo ====================================== >> "%LOG_FILE%"
echo Run started at %DATE% %TIME% >> "%LOG_FILE%"

REM --- Activate virtual environment ---
call "%VENV_DIR%\Scripts\activate.bat"

REM --- Sanity check ---
python --version >> "%LOG_FILE%" 2>&1
pip --version >> "%LOG_FILE%" 2>&1

REM --- Run script ---
python "%SCRIPT%" >> "%LOG_FILE%" 2>&1

REM --- Exit code ---
echo Exit code: %ERRORLEVEL% >> "%LOG_FILE%"
echo Run finished at %DATE% %TIME% >> "%LOG_FILE%"

REM --- Deactivate venv (optional) ---
deactivate

exit /b 0
