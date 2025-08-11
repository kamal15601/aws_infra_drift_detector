# Azure App Service Configuration
# https://docs.microsoft.com/en-us/azure/app-service/configure-language-python

# Startup command for Azure App Service
# This tells Azure which file to run
startup_command = "gunicorn --bind 0.0.0.0:$PORT main:app"

# Python version
python_version = "3.11"

# Environment variables needed for production
# Set these in Azure App Service Configuration -> Application Settings
required_env_vars = [
    "AZURE_STORAGE_ACCOUNT_NAME",  # Your Azure Storage Account name
    "AZURE_STORAGE_CONTAINER_NAME",  # Container name (default: uploads)
    "SECRET_KEY"  # Flask secret key for sessions
]
