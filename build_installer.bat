@echo off
echo ========================================
echo  TwinRain Document Processor Installer Builder
echo ========================================
echo.
echo This script will build the installer for TwinRain Document Processor.
echo.
echo Prerequisites:
echo  - Python 3.7 or higher
echo  - Required Python packages installed
echo  - NSIS installed
echo.
echo If you encounter any errors, please check README_INSTALLER.md
echo.
pause

python build_installer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo  Build process failed!
    echo  Please check the error messages above.
    echo ========================================
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo  Build completed successfully!
    echo  Installer is ready to distribute.
    echo ========================================
    echo.
    pause
    exit /b 0
) 