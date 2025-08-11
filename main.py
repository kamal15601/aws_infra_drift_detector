# Azure App Service deployment configuration
# This file tells Azure how to run your Python application

import os
from app import app  # Import your Flask app

if __name__ == "__main__":
    # For production deployment on Azure App Service
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
