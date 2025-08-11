#!/usr/bin/env python3
"""
Enhanced Drift Detection App Launcher
Supports both demo mode and real AWS integration
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'flask': 'flask',
        'boto3': 'boto3', 
        'azure-keyvault-secrets': 'azure.keyvault.secrets',
        'azure-identity': 'azure.identity',
        'requests': 'requests',
        'PyYAML': 'yaml'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them with:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_configuration():
    """Check configuration and provide guidance"""
    print("=== Configuration Check ===")
    
    # Check for config file
    config_file = Path("config.json")
    sample_config = Path("config.sample.json")
    
    if not config_file.exists() and sample_config.exists():
        print("⚠️  No config.json found, but config.sample.json exists")
        print("   Copy config.sample.json to config.json and customize it")
    
    # Check environment variables
    aws_vars = [
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION',
        'TERRAFORM_S3_BUCKET', 'TERRAFORM_S3_KEY'
    ]
    
    aws_configured = any(os.getenv(var) for var in aws_vars)
    
    if aws_configured:
        print("✅ AWS environment variables detected")
    else:
        print("⚠️  No AWS environment variables found")
        print("   Application will run in demo mode")
    
    # Check Azure Key Vault configuration
    keyvault_url = os.getenv('AZURE_KEYVAULT_URL')
    if keyvault_url:
        print("✅ Azure Key Vault configuration detected")
    else:
        print("ℹ️  No Azure Key Vault configuration found")
    
    return True

def run_tests():
    """Run basic tests to verify setup"""
    print("=== Running Tests ===")
    
    try:
        # Test configuration loading
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        app_config = config_manager.load_config()
        print("✅ Configuration loading successful")
        
        # Test AWS integration (if configured)
        try:
            from aws_integration import AWSIntegration
            aws_config = config_manager.get_aws_config()
            aws_integration = AWSIntegration(aws_config)
            
            result = aws_integration.test_connection()
            if result['success']:
                print("✅ AWS connection successful")
                print(f"   Connected as: {result.get('user_arn', 'Unknown')}")
            else:
                print("⚠️  AWS connection failed (will use demo mode)")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print("⚠️  AWS integration not available (will use demo mode)")
            print(f"   Reason: {e}")
        
        # Test drift engine
        from drift_engine import DriftDetectionEngine
        drift_engine = DriftDetectionEngine(app_config.__dict__)
        print("✅ Drift detection engine initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 AWS Terraform Drift Detection App")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    check_configuration()
    
    # Run tests
    if not run_tests():
        print("\n❌ Tests failed. Please check configuration.")
        sys.exit(1)
    
    print("\n=== Starting Application ===")
    
    # Determine which app to run
    enhanced_app = Path("drift_app_enhanced.py")
    original_app = Path("drift_app.py")
    
    if enhanced_app.exists():
        app_file = "drift_app_enhanced.py"
        print("🔧 Starting enhanced app with AWS integration support")
    elif original_app.exists():
        app_file = "drift_app.py"
        print("🔧 Starting original demo app")
    else:
        print("❌ No application file found")
        sys.exit(1)
    
    # Set environment for better development experience
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['PYTHONUNBUFFERED'] = '1'
    
    try:
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"🐍 Running: python {app_file}")
        print("🌐 Open http://localhost:5000 in your browser")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 50)
        
        # Run the application
        subprocess.run([sys.executable, app_file], env=env)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
