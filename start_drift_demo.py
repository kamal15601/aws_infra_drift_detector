"""
AWS Terraform Drift Detection Demo Launcher
Run this to start the demo without any AWS access required
"""

import subprocess
import sys
import os

def main():
    print("🚀 AWS Terraform Drift Detection Demo")
    print("=" * 50)
    print()
    print("✅ This demo version includes:")
    print("   • Realistic mock Terraform state data")
    print("   • Simulated AWS resource scanning")
    print("   • Live drift detection every 5 minutes")
    print("   • Complete alert processing system")
    print("   • Interactive web dashboard")
    print()
    print("🔧 No AWS access or credentials required!")
    print("📊 All data is simulated for demonstration")
    print()
    
    choice = input("Start the drift detection demo? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        print("\n🔄 Starting AWS Terraform Drift Detection Demo...")
        print("📱 Open http://localhost:5000 in your browser")
        print("⏰ Background scanner will run every 5 minutes")
        print("🔍 New drift will be detected automatically")
        print()
        print("Press Ctrl+C to stop the application")
        print("=" * 50)
        
        # Start the Flask application
        os.system('"C:/Users/2309301/OneDrive - Cognizant/Desktop/staticapp/.venv/Scripts/python.exe" drift_app.py')
    else:
        print("Demo cancelled. Run again when ready!")

if __name__ == "__main__":
    main()
