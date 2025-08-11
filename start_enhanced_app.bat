@echo off
echo.
echo AWS Terraform Drift Detection App - Enhanced Version
echo =====================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Checking Python version...
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

REM Check if required files exist
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Please run this script from the application directory
    pause
    exit /b 1
)

echo.
echo Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

REM Check configuration
echo Checking configuration...
if exist "config.sample.json" (
    if not exist "config.json" (
        echo INFO: config.sample.json found but config.json is missing
        echo You can copy config.sample.json to config.json and customize it
        echo.
    )
)

REM Check environment variables
set "AWS_CONFIGURED=false"
if defined AWS_ACCESS_KEY_ID set "AWS_CONFIGURED=true"
if defined AWS_DEFAULT_REGION set "AWS_CONFIGURED=true"
if defined TERRAFORM_S3_BUCKET set "AWS_CONFIGURED=true"

if "%AWS_CONFIGURED%"=="true" (
    echo INFO: AWS environment variables detected - production mode available
) else (
    echo INFO: No AWS environment variables found - will run in demo mode
)

echo.
echo Starting the enhanced drift detection application...
echo.
echo The application will be available at: http://localhost:5000
echo Press Ctrl+C to stop the application
echo.

REM Start the application
if exist "drift_app_enhanced.py" (
    echo Running enhanced application...
    python drift_app_enhanced.py
) else if exist "drift_app.py" (
    echo Running original application...
    python drift_app.py
) else (
    echo ERROR: No application file found
    echo Please ensure drift_app_enhanced.py or drift_app.py exists
    pause
    exit /b 1
)

echo.
echo Application stopped.
pause
