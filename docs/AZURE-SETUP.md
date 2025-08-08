# Azure Portal Setup Guide - Step by Step

This guide walks you through creating and deploying your InfraSnap Static Web App using only the Azure Portal - no command line tools required.

## 🎯 Prerequisites

- Azure subscription (free tier works fine)
- The source files from this deployment package
- Web browser

## 📋 Step-by-Step Instructions

### Step 1: Access Azure Portal

1. Open your web browser
2. Go to [portal.azure.com](https://portal.azure.com)
3. Sign in with your Azure account

### Step 2: Create Static Web App

1. **Click "Create a resource"** (+ icon in top left)
2. **Search for "Static Web Apps"**
3. **Click "Static Web Apps"** from the results
4. **Click "Create"**

### Step 3: Configure Basic Settings

Fill out the form with these settings:

**Basics Tab:**
- **Subscription**: Choose your subscription
- **Resource Group**: 
  - Click "Create new"
  - Name it: `rg-infrasnap`
- **Name**: `infrasnap-webapp` (must be globally unique)
- **Plan type**: `Free` (perfect for testing)
- **Azure Functions and staging slots**: `Enabled`
- **Region**: Choose closest to you (e.g., `East US 2`)

**Deployment Tab:**
- **Source**: Select `Other`
- Leave GitHub settings empty since we're deploying manually

### Step 4: Review and Create

1. **Click "Review + create"**
2. **Verify your settings**
3. **Click "Create"**
4. **Wait for deployment** (usually takes 2-3 minutes)

### Step 5: Get Deployment Information

After creation:

1. **Click "Go to resource"**
2. **Copy the URL** - This is your app's web address
3. **Click "Manage deployment token"**
4. **Copy the deployment token** - Save this for later

Your URLs will look like:
- **App URL**: `https://infrasnap-webapp.azurestaticapps.net`
- **Deployment Token**: `0123456789abcdef...` (long string)

## 🚀 Deployment Methods

### Method 1: Using GitHub (Easiest)

**Step 1: Create GitHub Repository**
1. Go to [github.com](https://github.com) and sign in
2. Click "New repository"
3. Name it: `infrasnap-static-app`
4. Make it public
5. Click "Create repository"

**Step 2: Upload Files**
1. **Upload all files from the `src` folder**:
   - `index.html`
   - `styles.css`
   - `app.js`
2. **Commit the files**

**Step 3: Connect to Azure**
1. **Go back to Azure Portal**
2. **Go to your Static Web App resource**
3. **Click "Deployment" in the left menu**
4. **Click "Configure"**
5. **Choose "GitHub"**
6. **Authorize Azure to access GitHub**
7. **Select your repository**
8. **Build settings**:
   - **App location**: `/`
   - **API location**: (leave empty)
   - **Output location**: `/`
9. **Click "Save"**

GitHub Actions will automatically deploy your app!

### Method 2: Using Azure CLI (Advanced Users)

If you have Azure CLI installed:

```bash
# Install Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

# Navigate to your src folder
cd path/to/deployment-package/src

# Deploy using your deployment token
swa deploy . --deployment-token YOUR_DEPLOYMENT_TOKEN_HERE
```

### Method 3: VS Code Extension

**Step 1: Install Extension**
1. Open VS Code
2. Install "Azure Static Web Apps" extension
3. Sign in to Azure

**Step 2: Deploy**
1. Open the `src` folder in VS Code
2. Right-click in the explorer
3. Select "Deploy to Static Web App"
4. Choose your Static Web App
5. Confirm deployment

## ✅ Verify Deployment

### Check Your App

1. **Open the app URL** from Step 5 above
2. **You should see**: InfraSnap homepage with gradient background
3. **Test navigation**: Click menu items
4. **Test dashboard**: Click "View Dashboard" button
5. **Test report**: Click "Generate Report" button

### Expected Behavior

✅ **Homepage loads** with hero section  
✅ **Navigation works** smoothly  
✅ **Dashboard shows** stats and activity  
✅ **Reports download** as markdown files  
✅ **Mobile responsive** design  
✅ **No JavaScript errors** in browser console  

## 🔧 Configure Additional Settings

### Custom Domain (Optional)

1. **Go to your Static Web App** in Azure Portal
2. **Click "Custom domains"**
3. **Click "Add"**
4. **Enter your domain name**
5. **Follow DNS configuration instructions**
6. **Azure provides free SSL certificate**

### Environment Variables

1. **Go to "Configuration"** in Azure Portal
2. **Click "Application settings"**
3. **Add any environment variables** you need:
   - `ENVIRONMENT=production`
   - `API_URL=https://your-api.com`

### Authentication (Optional)

1. **Go to "Authentication"** in Azure Portal
2. **Click "Manage providers"**
3. **Choose providers**: Azure AD, GitHub, Google, etc.
4. **Configure as needed**

## 📊 Monitoring and Logs

### View Logs

1. **Go to "Log stream"** in Azure Portal
2. **See real-time logs** of your application
3. **Check for any errors** or issues

### Application Insights

1. **Create Application Insights** resource
2. **Link it to your Static Web App**
3. **Monitor performance** and usage

## 🆘 Troubleshooting

### App Not Loading

**Check:**
- URL is correct and accessible
- Files uploaded properly
- No browser console errors
- DNS propagation (if using custom domain)

**Solutions:**
- Clear browser cache
- Try incognito/private window
- Check Azure portal for deployment status
- Verify all files are present

### Deployment Issues

**GitHub Method:**
- Check GitHub Actions tab for build status
- Verify file paths in repository
- Ensure all files committed

**Manual Method:**
- Verify deployment token is correct
- Check file permissions
- Ensure CLI tools are latest version

### Performance Issues

**Common Fixes:**
- Enable CDN in Azure
- Optimize images
- Minify CSS/JavaScript
- Check network connectivity

## 🎉 Success Checklist

- [ ] Static Web App created in Azure
- [ ] Source files deployed successfully
- [ ] App loads at provided URL
- [ ] All features work (navigation, dashboard, reports)
- [ ] Mobile responsive design works
- [ ] No console errors
- [ ] Custom domain configured (if desired)
- [ ] Monitoring set up (if desired)

## 📞 Next Steps

1. **Share your app URL** with team members
2. **Set up monitoring** for production use
3. **Plan regular updates** and maintenance
4. **Consider authentication** if needed
5. **Connect to real APIs** when backend is ready

Your InfraSnap application is now live on Azure! 🎊
