#!/usr/bin/env python3
"""
Quick start script for InfraSnap Python 3.9 application
Run this to start the development server
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def start_server():
    """Start the Flask development server"""
    print("Starting InfraSnap Python 3.9 server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Set environment variables
        os.environ['FLASK_APP'] = 'app.py'
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = 'True'
        
        # Start the Flask app
        subprocess.check_call([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main function"""
    print("🚀 InfraSnap Python 3.9 Quick Start")
    print("===================================")
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ app.py not found. Please run this script from the project directory.")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required. Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
