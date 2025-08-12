# 🚀 Python File Upload for Azure App Service

A production-ready Python Flask application for uploading files to Azure App Service with two storage options:

1. **Local Storage** - Simple but files may be lost during restarts
2. **Azure Blob Storage** - Production-ready with persistent storage

## 📁 Project Structure

```
staticapp/
├── app.py                  # Flask app with local storage
├── app_blob.py            # Flask app with Azure Blob Storage
├── main.py                # Production entry point
├── start.py               # Development startup script
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html         # Upload form (local storage)
│   ├── files.html         # File list (local storage)
│   ├── index_blob.html    # Upload form (blob storage)
│   └── files_blob.html    # File list (blob storage)
└── uploads/               # Local upload directory
```

## 🔧 Local Development Setup

### 1. Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt
```

### 2. Run the Application

```powershell
# Option 1: Use the startup script (recommended)
python start.py

# Option 2: Run directly
python app.py              # For local storage
python app_blob.py         # For Azure Blob Storage
```

### 3. Access the Application

Open your browser and go to: `http://localhost:5000`

## ☁️ Azure App Service Deployment

### Option 1: Local Storage (Simple)

**Pros:**
- ✅ No additional Azure services needed
- ✅ Zero configuration
- ✅ Works immediately

**Cons:**
- ❌ Files lost during app restarts/deployments
- ❌ Limited storage space
- ❌ No backup/redundancy

**Deployment Steps:**
1. Deploy your code to Azure App Service
2. Set startup command: `gunicorn --bind 0.0.0.0:$PORT app:app`
3. Ready to use!

### Option 2: Azure Blob Storage (Recommended)

**Pros:**
- ✅ Files persist through restarts
- ✅ Unlimited scalable storage
- ✅ Built-in backup and redundancy
- ✅ Enterprise security

**Cons:**
- ⚠️ Requires additional Azure setup

**Setup Steps:**

#### 1. Create Azure Storage Account
```bash
# Using Azure CLI
az storage account create \
    --name yourstorageaccount \
    --resource-group your-resource-group \
    --location eastus \
    --sku Standard_LRS
```

#### 2. Create Storage Container
```bash
az storage container create \
    --name uploads \
    --account-name yourstorageaccount
```

#### 3. Enable Managed Identity
```bash
# Enable system-assigned managed identity for your App Service
az webapp identity assign \
    --name your-app-name \
    --resource-group your-resource-group
```

#### 4. Grant Storage Permissions
```bash
# Get the principal ID of your App Service
PRINCIPAL_ID=$(az webapp identity show \
    --name your-app-name \
    --resource-group your-resource-group \
    --query principalId -o tsv)

# Grant Storage Blob Data Contributor role
az role assignment create \
    --assignee $PRINCIPAL_ID \
    --role "Storage Blob Data Contributor" \
    --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/your-resource-group/providers/Microsoft.Storage/storageAccounts/yourstorageaccount"
```

#### 5. Configure App Service Settings
In Azure Portal → App Service → Configuration → Application Settings:

```
AZURE_STORAGE_ACCOUNT_NAME = yourstorageaccount
AZURE_STORAGE_CONTAINER_NAME = uploads
SECRET_KEY = your-secret-key-here
```

#### 6. Set Startup Command
In Azure Portal → App Service → Configuration → General Settings:

```
Startup Command: gunicorn --bind 0.0.0.0:$PORT app_blob:app
```

## 🔍 Testing the Deployment

### Health Check Endpoint
Visit: `https://your-app.azurewebsites.net/health`

**Local Storage Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-08-08T10:30:00"
}
```

**Blob Storage Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-08-08T10:30:00",
    "storage_status": "connected",
    "storage_account": "yourstorageaccount",
    "container": "uploads"
}
```

## 📋 Supported File Types

- **Documents:** TXT, PDF, DOC, DOCX
- **Images:** PNG, JPG, JPEG, GIF
- **Maximum Size:** 16MB per file

## 🔒 Security Features

- ✅ File type validation
- ✅ Secure filename handling
- ✅ Size limits enforced
- ✅ Managed Identity authentication (Blob Storage)
- ✅ HTTPS encryption in production

## 🚀 Features

- **Clean UI:** Modern, responsive web interface
- **File Management:** Upload, view, and download files
- **Error Handling:** Comprehensive error messages
- **Logging:** Detailed application logs
- **Health Monitoring:** Built-in health check endpoint

## 🔧 Troubleshooting

### Common Issues

**1. Storage Account Connection Fails**
- Verify Managed Identity is enabled
- Check RBAC permissions
- Ensure storage account name is correct

**2. Files Not Uploading**
- Check file size (max 16MB)
- Verify file type is allowed
- Check application logs

**3. Downloads Not Working**
- Verify blob exists in storage
- Check network connectivity
- Review error logs

### Logs Location
- **Local Development:** Console output
- **Azure App Service:** Log Stream in Azure Portal

## 📊 Monitoring

Monitor your application using:
- Azure Application Insights
- Azure Monitor Logs
- Built-in App Service metrics

## 💡 Next Steps

1. **Add User Authentication** - Integrate Azure AD
2. **Implement File Sharing** - Add user-specific folders
3. **Add Metadata Storage** - Use Azure SQL Database
4. **Enable CDN** - Add Azure CDN for global access
5. **Implement Virus Scanning** - Add Azure Defender

## 🤝 Contributing

Feel free to contribute improvements:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

# AWS Infrastructure Drift Detection WebApp

## Overview
This web application helps you monitor and detect configuration drift in your AWS infrastructure by comparing live AWS resources with your Terraform state. It provides real-time alerts, scan history, and a user-friendly dashboard for cloud operations and DevOps teams.

## Features
- Real-time AWS drift detection
- Dashboard with scan results and alert statistics
- View all active alerts with filtering and search
- Export alerts as CSV
- Acknowledge, suppress, and resolve alerts
- Settings page to securely configure AWS credentials
- Health check endpoint
- Responsive, modern UI with notifications and error handling

## How to Install & Run
1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd staticapp
   ```
2. **Install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run the app:**
   ```bash
   python main.py
   ```
4. **Access the webapp:**
   Open your browser and go to `http://localhost:5000`

## How to Configure AWS Credentials
- Click the **Settings** button in the navigation bar.
- Enter your AWS Access Key ID, Secret Access Key, and Region.
- Click **Save Settings**. Credentials are securely stored in `config.json`.

## How to Use
- **Dashboard:** View drift detection status and scan history.
- **Alerts:** See all active alerts, filter by severity, search, and take actions.
- **Export:** Download all alerts as CSV for reporting or analysis.
- **Settings:** Update AWS credentials anytime.
- **Health:** Check app status and integration.

## Security Notes
- AWS credentials are stored locally in `config.json` and used only for scanning.
- Never share your credentials. Use IAM roles and least privilege for production.

## Troubleshooting
- If alerts do not show, check your AWS credentials and scan history.
- For deployment issues, verify Python version and dependencies.
- For API errors, check network and AWS permissions.

## License
MIT

## Contact
For support or feature requests, open an issue on GitHub or contact the maintainer.
