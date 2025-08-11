"""
Simple startup script to test the application locally
Choose between local storage or Azure Blob Storage
"""

import sys
import os

def main():
    print("🚀 Azure App Service File Upload Application")
    print("=" * 50)
    print()
    print("Choose your storage option:")
    print("1. Local Storage (app.py) - Simple but files may be lost")
    print("2. Azure Blob Storage (app_blob.py) - Production ready")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n🔄 Starting with Local Storage...")
        print("⚠️  WARNING: Files will be lost during app restarts!")
        os.system("python app.py")
    elif choice == "2":
        print("\n☁️  Starting with Azure Blob Storage...")
        print("ℹ️  Make sure you have configured Azure Storage Account and Managed Identity")
        os.system("python app_blob.py")
    else:
        print("❌ Invalid choice. Please run the script again.")
        return

if __name__ == "__main__":
    main()
