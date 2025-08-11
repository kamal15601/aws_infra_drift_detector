@echo off
echo 🚀 AWS Terraform Drift Detection Demo
echo ==================================================
echo.
echo ✅ This demo includes:
echo    • Mock Terraform state files
echo    • Simulated AWS resource scanning  
echo    • Real-time drift detection every 5 minutes
echo    • Complete alert processing system
echo    • Interactive web dashboard
echo.
echo 🔧 No AWS access required!
echo 📊 All data is simulated for demonstration
echo.
set /p choice="Start the drift detection demo? (y/n): "

if /i "%choice%"=="y" (
    echo.
    echo 🔄 Starting AWS Terraform Drift Detection Demo...
    echo 📱 Open http://localhost:5000 in your browser
    echo ⏰ Background scanner runs every 5 minutes
    echo 🔍 New drift detected automatically
    echo.
    echo Press Ctrl+C to stop the application
    echo ==================================================
    ".venv\Scripts\python.exe" drift_app.py
) else (
    echo Demo cancelled. Run again when ready!
    pause
)

pause
