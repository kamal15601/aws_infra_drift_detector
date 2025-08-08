# InfraSnap Static Web App - Manual Deployment Guide

This package contains everything you need to manually deploy the InfraSnap Static Web App to Azure.

## 📁 Package Contents

```
deployment-package/
├── src/                    # Source code for the static web app
│   ├── index.html         # Main HTML file
│   ├── styles.css         # CSS styles and animations
│   └── app.js             # JavaScript application logic
├── docs/                  # Documentation
│   ├── DEPLOYMENT.md      # This file - deployment instructions
│   └── AZURE-SETUP.md     # Detailed Azure portal setup guide
└── README.md              # Quick start guide
```

## 🚀 Deployment Options

### Option 1: Azure Static Web Apps (Recommended)

**Step 1: Create Static Web App in Azure Portal**

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Static Web Apps" and select it
4. Click "Create"
5. Fill in the details:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or use existing
   - **Name**: `infrasnap-swa` (or your preferred name)
   - **Plan type**: Free (for testing) or Standard (for production)
   - **Region**: Choose closest to your users
   - **Source**: Other (since we're deploying manually)

6. Click "Review + create" then "Create"

**Step 2: Deploy Your Files**

After the Static Web App is created:

1. Go to your Static Web App resource
2. Click "Overview" to see the default URL
3. Click "Manage deployment token" and copy the deployment token
4. Use one of these methods to deploy:

#### Method A: Using Azure CLI (Preferred)
```bash
# Install Azure Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

# Deploy using the deployment token
swa deploy ./src --deployment-token <YOUR_DEPLOYMENT_TOKEN>
```

#### Method B: Using GitHub Integration
1. Upload your `src` folder to a GitHub repository
2. In Azure portal, go to your Static Web App
3. Click "Manage deployment token"
4. Set up GitHub Actions integration
5. Configure the build settings:
   - **App location**: `/`
   - **Api location**: (leave empty)
   - **Output location**: `/`

#### Method C: Manual File Upload via VS Code
1. Install Azure Static Web Apps extension in VS Code
2. Sign in to Azure
3. Right-click your `src` folder
4. Select "Deploy to Static Web App"
5. Choose your Static Web App resource

### Option 2: Azure Storage Static Website

**Step 1: Create Storage Account**

1. Go to Azure Portal
2. Create a Storage Account
3. Enable "Static website" in the storage account settings
4. Set index document to `index.html`
5. Note the primary endpoint URL

**Step 2: Upload Files**

Use Azure Storage Explorer or Azure CLI:
```bash
# Using Azure CLI
az storage blob upload-batch -s ./src -d '$web' --account-name <storage-account-name>
```

### Option 3: Azure App Service

**Step 1: Create App Service**

1. Create new App Service in Azure Portal
2. Choose "Code" deployment
3. Runtime stack: Node.js (or any static option)
4. Operating System: Windows or Linux

**Step 2: Deploy Files**

1. Use deployment center in Azure Portal
2. Upload files via FTP
3. Or use VS Code Azure App Service extension

## 🔧 Configuration

### Environment Variables

If you need to add environment variables or API endpoints later:

1. Go to your deployed app settings
2. Add configuration values:
   - `API_BASE_URL`: Your backend API URL
   - `ENVIRONMENT`: production/staging
   - Any other custom settings

### Custom Domain (Optional)

1. In Azure Portal, go to your Static Web App
2. Click "Custom domains"
3. Add your domain and configure DNS
4. Azure will provide SSL certificate automatically

## 📊 Monitoring Setup

The app includes Application Insights integration points. To enable monitoring:

1. Create Application Insights resource
2. Get the instrumentation key
3. Add it to your app configuration
4. Monitor usage, performance, and errors

## 🔐 Security Configuration

### HTTPS
- Automatically enabled for Azure Static Web Apps
- Custom SSL certificates supported for custom domains

### Authentication (Optional)
- Azure Static Web Apps supports built-in authentication
- Configure providers: Azure AD, GitHub, Google, Facebook, Twitter

### Access Control
- Set up route-based access control in staticwebapp.config.json
- Configure role-based access if needed

## 🧪 Testing Your Deployment

After deployment:

1. **Access the app**: Use the provided URL from Azure
2. **Test functionality**:
   - Navigation between sections
   - Dashboard interactions
   - Report generation
   - Responsive design on mobile
3. **Check console**: Open browser dev tools for any errors
4. **Performance**: Test loading speed and responsiveness

## 📈 Post-Deployment

### Performance Optimization
- Enable CDN for faster global access
- Optimize images and assets
- Monitor Core Web Vitals

### Maintenance
- Set up monitoring alerts
- Plan for regular updates
- Monitor usage analytics

## 🆘 Troubleshooting

### Common Issues

**App not loading:**
- Check browser console for errors
- Verify all files uploaded correctly
- Ensure file paths are correct

**Styling issues:**
- Verify CSS file is loaded
- Check for MIME type issues
- Ensure font awesome CDN is accessible

**JavaScript errors:**
- Check browser compatibility
- Verify all scripts loaded
- Test in different browsers

### Getting Help

1. Check Azure documentation
2. Review Azure portal logs
3. Test locally first using `python -m http.server 8000`
4. Check network tab in browser dev tools

## 🎯 Next Steps

1. **Deploy the app** using your preferred method
2. **Test thoroughly** in production environment
3. **Set up monitoring** for performance tracking
4. **Configure custom domain** if needed
5. **Add authentication** if required
6. **Integrate with backend APIs** when ready

Your InfraSnap Static Web App is ready for production! 🚀
