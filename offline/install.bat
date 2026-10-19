@echo off
REM ---------------------------------------------------------------------------
REM Offline installer for file_flag (Windows, Python 3.11, 64-bit)
REM Installs everything from the bundled .\wheels folder with NO internet.
REM ---------------------------------------------------------------------------
setlocal
set "WHEELS=%~dp0wheels"

echo Using wheels in: %WHEELS%
echo.

REM Make sure python is on PATH
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: 'python' was not found on PATH. Install Python 3.11 (64-bit) first.
    exit /b 1
)

echo [1/2] Upgrading pip / setuptools / wheel from the local folder...
python -m pip install --no-index --find-links "%WHEELS%" --upgrade pip setuptools wheel
if errorlevel 1 goto :fail

echo.
echo [2/2] Installing file_flag and its dependencies...
python -m pip install --no-index --find-links "%WHEELS%" file_flag==0.1.1
if errorlevel 1 goto :fail

echo.
echo Done. Verify with:  python -m file_flag --help
exit /b 0

:fail
echo.
echo Offline install FAILED. Check that Python is 3.11 64-bit and the wheels
echo folder is present next to this script.
exit /b 1
