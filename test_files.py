#!/usr/bin/env python3
"""
Test script to verify all files are accessible
Run this to check if your CSS and JS files are being served correctly
"""

import requests
import sys
from urllib.parse import urljoin

def test_file_access(base_url="http://localhost:8000"):
    """Test if all files are accessible"""
    
    print("🧪 Testing InfraSnap File Access")
    print("================================")
    
    # Files to test
    test_files = [
        ("/", "Main HTML page"),
        ("/styles.css", "CSS stylesheet"),
        ("/app.js", "JavaScript application"),
        ("/health", "Health check API"),
        ("/api/dashboard", "Dashboard API"),
        ("/api/activities", "Activities API")
    ]
    
    success_count = 0
    total_count = len(test_files)
    
    for path, description in test_files:
        url = urljoin(base_url, path)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: {url} - OK")
                success_count += 1
            else:
                print(f"❌ {description}: {url} - Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {description}: {url} - Server not running")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: {url} - Error: {e}")
    
    print(f"\n📊 Results: {success_count}/{total_count} files accessible")
    
    if success_count == total_count:
        print("🎉 All files are working perfectly!")
        return True
    else:
        print("⚠️ Some files are not accessible. Check server logs.")
        return False

def check_file_structure():
    """Check if all required files exist"""
    import os
    
    print("\n📁 Checking File Structure")
    print("==========================")
    
    required_files = [
        "app.py",
        "src/index.html",
        "src/styles.css", 
        "src/app.js",
        "requirements.txt"
    ]
    
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} - Found")
        else:
            print(f"❌ {file_path} - Missing")
            all_exist = False
    
    return all_exist

def main():
    """Main test function"""
    print("🚀 InfraSnap File Verification")
    print("==============================\n")
    
    # Check file structure first
    if not check_file_structure():
        print("\n❌ Some required files are missing!")
        sys.exit(1)
    
    print("\n✅ All required files found!")
    
    # Test server access
    print("\n🌐 Testing Server Access")
    print("Make sure your server is running: python app.py")
    print("Then press Enter to test, or Ctrl+C to cancel...")
    
    try:
        input()
        success = test_file_access()
        
        if success:
            print("\n🎉 SUCCESS! Your Python 3.9 application is working perfectly!")
            print("Your CSS and JS files are being served correctly.")
        else:
            print("\n⚠️ Some issues detected. Check the server output for errors.")
            
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")

if __name__ == "__main__":
    main()
