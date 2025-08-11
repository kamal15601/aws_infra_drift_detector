# 🚨 AWS Terraform Drift Detection Demo

A complete **AWS infrastructure drift detection system** that monitors differences between your Terraform state files and live AWS resources. This demo version runs without requiring AWS access or credentials - perfect for testing and demonstration!

## 🎯 What This Demo Shows

### **Complete Drift Detection Workflow:**
- 📋 **Terraform State Analysis** - Parses `.tfstate` files from S3 backend
- 🔍 **AWS Resource Scanning** - Simulates scanning live AWS infrastructure  
- ⚠️ **Drift Detection** - Compares state vs reality and identifies changes
- 🚨 **Real-time Alerts** - Processes and routes alerts based on severity
- 📊 **Interactive Dashboard** - Modern web interface with live updates
- ⏰ **Automated Monitoring** - Runs scans every 5 minutes automatically

### **Real-World Scenarios Simulated:**
- 🖥️ **Configuration Drift** - Instance size changed manually (t3.medium → t3.large)
- 🔒 **Security Changes** - SSH rule added to security group outside Terraform
- 🪣 **Storage Modifications** - S3 encryption method changed (AES256 → KMS)
- 🏷️ **Tag Management** - Tags added/removed manually
- 📦 **Unmanaged Resources** - Resources created outside Terraform

## 🚀 Quick Start (No AWS Required!)

### **Method 1: Double-click to Run**
```bash
# Windows
start_drift_demo.bat

# Or Python
python start_drift_demo.py
```

### **Method 2: Direct Launch**
```bash
python drift_app.py
```

### **Access the Application**
Open your browser to: **http://localhost:5000**

## 📊 Dashboard Features

### **Main Dashboard (`/`)**
- 📈 Real-time statistics (resources monitored, drift detected, active alerts)
- 🔍 Latest scan results with detailed breakdown
- 🚨 Active alerts panel with severity indicators
- ⚙️ System status and next scan information
- 🔄 Manual scan trigger capability

### **Detailed Scan Results (`/scan-results`)**
- 📋 Complete drift analysis with expandable details
- 🎯 Resource-by-resource comparison (Terraform vs AWS)
- 📊 Visual difference highlighting
- 💡 Impact assessment for each change
- 🔧 Suggested remediation actions

### **Alert Management (`/alerts`)**
- 🔔 Comprehensive alert center with filtering
- 📱 Alert severity and status management
- 🔍 Search and filter capabilities
- ✅ Alert acknowledgment and resolution
- 📈 Alert statistics and trends

## 🎭 Demo Data Overview

### **Mock Infrastructure:**
```yaml
Simulated AWS Resources:
  - EC2 Instance: web-server-prod (with drift - size changed)
  - Security Group: web-server-sg (with drift - SSH rule added)
  - S3 Bucket: app-data-bucket (with drift - encryption changed)
  - Manual Instance: test-instance (not in Terraform)

Terraform State:
  - Source: s3://terraform-state-bucket/production/terraform.tfstate
  - Version: 4 (Terraform 1.5.0)
  - Resources: 3 managed resources
  - Regions: us-east-1
```

### **Generated Alerts:**
- 🔴 **CRITICAL**: SSH access rule added to security group
- 🟠 **HIGH**: EC2 instance size changed (cost impact)
- 🔵 **MEDIUM**: S3 encryption method changed
- 🔵 **MEDIUM**: Unmanaged resource detected

## ⏰ Automated Scanning

### **5-Minute Monitoring Cycle:**
```python
Every 5 minutes the system:
1. 📥 Checks for Terraform state changes (S3 ETag simulation)
2. 🔍 Scans AWS resources (simulated API calls)
3. 📊 Compares state vs live configuration
4. 🚨 Generates alerts for detected drift
5. 📱 Updates dashboard with real-time data
6. 🔔 Sends notifications (simulated)
```

### **Background Processing:**
- ✅ Runs automatically in background thread
- 📊 Stores results in local JSON files
- 🔄 Updates dashboard every 30 seconds
- 📈 Maintains 7-day history (configurable)

## 🎯 Alert Processing System

### **Alert Severity Logic:**
```python
CRITICAL: Security-related changes (IAM, security groups, KMS)
HIGH:     Production resource modifications
MEDIUM:   Configuration changes with business impact
LOW:      Tag changes and minor modifications
```

### **Alert Lifecycle:**
- 🆕 **NEW** - Just detected, needs attention
- ✅ **ACKNOWLEDGED** - Someone is investigating
- 🔧 **IN_PROGRESS** - Being remediated
- ✔️ **RESOLVED** - Fixed and verified
- 🔇 **SUPPRESSED** - Intentionally ignored

### **Smart Features:**
- 🔄 **Deduplication** - Prevents alert spam
- 📊 **Correlation** - Groups related changes
- ⏰ **Auto-resolution** - Resolves when drift is fixed
- 📈 **Trending** - Tracks patterns over time

## 🗂️ File Structure

```
staticapp/
├── drift_app.py                 # Main Flask application
├── start_drift_demo.py         # Demo launcher
├── start_drift_demo.bat        # Windows batch launcher
├── requirements.txt             # Python dependencies
├── templates/
│   ├── dashboard.html          # Main dashboard
│   ├── scan_results.html       # Detailed scan results
│   └── alerts.html             # Alert management
├── data/                       # Local storage (auto-created)
│   ├── scans/                  # Individual scan results
│   ├── alerts/                 # Alert data
│   └── latest_scan.json        # Current scan status
└── README_DRIFT_DEMO.md        # This file
```

## 🔧 Production Transition

### **When Ready for Real AWS:**
1. **Add AWS Credentials** - IAM roles or access keys
2. **Configure S3 Backend** - Point to your state bucket
3. **Update Resource Types** - Add specific AWS services you use
4. **Set Alert Channels** - Slack, email, Teams integration
5. **Deploy to Azure** - Use Azure App Service + Functions

### **Current Demo vs Production:**
| Feature | Demo Version | Production Version |
|---------|-------------|-------------------|
| **Data Source** | Mock JSON files | Real AWS APIs + S3 |
| **Storage** | Local files | Azure SQL/Cosmos DB |
| **Scheduling** | Background thread | Azure Functions |
| **Alerts** | Simulated | Real Slack/email |
| **Auth** | None required | AWS IAM roles |

## 🎨 Technology Stack

### **Backend:**
- 🐍 **Python 3.13** with Flask web framework
- 📊 **APScheduler** for background task scheduling
- 🗄️ **JSON files** for data storage (demo)
- 🔄 **Threading** for concurrent processing

### **Frontend:**
- 🎨 **Modern CSS** with responsive design
- ⚡ **JavaScript** for real-time updates
- 📱 **Mobile-friendly** interface
- 🎯 **Interactive** charts and filters

### **Demo Features:**
- 🚀 **Zero dependencies** - no AWS setup required
- 📊 **Realistic data** - based on actual AWS resources
- ⏰ **Live simulation** - new drift appears over time
- 🔧 **Full functionality** - complete user experience

## 📈 Monitoring & Observability

### **Built-in Health Checks:**
- 🔍 **Health endpoint** (`/health`) - System status
- 📊 **API endpoints** - Latest scan data
- 📱 **Real-time updates** - Dashboard auto-refresh
- 📝 **Comprehensive logging** - Debug and audit trails

### **Performance Metrics:**
- ⏱️ **Scan duration** - How long each scan takes
- 📊 **Resource counts** - Total resources monitored
- 🚨 **Alert statistics** - Volume and resolution rates
- 📈 **Trend analysis** - Drift patterns over time

## 🚀 Next Steps

### **Try the Demo:**
1. Run `start_drift_demo.bat` or `python drift_app.py`
2. Open http://localhost:5000 in your browser
3. Explore the dashboard and see simulated drift
4. Wait 5 minutes to see automatic scanning in action
5. Check the alerts page for detected changes

### **For Production Deployment:**
1. Review the mock data to understand the workflow
2. Configure your AWS credentials and S3 backend
3. Customize resource types for your infrastructure
4. Set up alert channels (Slack, email, Teams)
5. Deploy to Azure App Service with Azure Functions

---

## 🎉 Demo Highlights

**This demo gives you a complete picture of:**
- ✅ How drift detection works in practice
- ✅ What the user interface looks like
- ✅ How alerts are processed and managed
- ✅ What kind of data you'll see in production
- ✅ How the system scales and performs

**Perfect for:**
- 👥 **Team demonstrations** - Show stakeholders the value
- 🧪 **Testing workflows** - Understand the user experience  
- 📋 **Requirements gathering** - See what features you need
- 🎯 **Proof of concept** - Validate the approach
- 🚀 **Getting started** - Learn before implementing

Start the demo and explore the full drift detection experience! 🚀
