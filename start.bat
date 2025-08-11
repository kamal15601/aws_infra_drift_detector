@echo off
echo 🚀 Starting Python File Upload Application
echo.
echo Choose your storage option:
echo 1. Local Storage (simple, files may be lost)
echo 2. Azure Blob Storage (production ready)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo 🔄 Starting with Local Storage...
    echo ⚠️  WARNING: Files will be lost during app restarts!
    echo.
    ".venv\Scripts\python.exe" app.py
) else if "%choice%"=="2" (
    echo.
    echo ☁️  Starting with Azure Blob Storage...
    echo ℹ️  Make sure you have configured Azure Storage Account and Managed Identity
    echo.
    ".venv\Scripts\python.exe" app_blob.py
) else (
    echo ❌ Invalid choice. Please run the script again.
    pause
)

pause
