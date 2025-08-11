# 🔐 AWS Setup Guide - Connecting to Your Real AWS Account

This guide shows you exactly how to configure the drift detection app to connect to your actual AWS account and S3 bucket containing your Terraform state files.

## 📋 **Configuration Overview**

You have **3 main options** for AWS authentication and **1 required configuration** for the S3 state file:

### Option 1: AWS Profile (Recommended for Development)
### Option 2: Environment Variables  
### Option 3: Direct Credentials in config.json
### Option 4: IAM Role Assumption

---

## 🔧 **Step 1: Configure Your S3 State File Access**

**REQUIRED**: Update these settings in `config.json`:

```json
{
  "terraform_s3_bucket": "your-terraform-state-bucket-name",
  "terraform_s3_key": "path/to/your/terraform.tfstate",
  "terraform_s3_region": "us-east-1"
}
```

**Example:**
```json
{
  "terraform_s3_bucket": "mycompany-terraform-state",
  "terraform_s3_key": "production/infrastructure/terraform.tfstate", 
  "terraform_s3_region": "us-east-1"
}
```

---

## 🔑 **Step 2: Choose Your AWS Authentication Method**

### **Option 1: AWS Profile (Recommended for Development)**

1. **Configure AWS CLI** (if not already done):
   ```powershell
   aws configure --profile myprofile
   ```
   
2. **Update config.json**:
   ```json
   {
     "aws_profile": "myprofile",
     "aws_region": "us-east-1"
   }
   ```

3. **Set environment variable**:
   ```powershell
   $env:AWS_PROFILE = "myprofile"
   ```

### **Option 2: Environment Variables (Recommended for Production)**

1. **Set environment variables**:
   ```powershell
   $env:AWS_ACCESS_KEY_ID = "AKIA..."
   $env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
   $env:AWS_DEFAULT_REGION = "us-east-1"
   
   # Optional: For temporary credentials
   $env:AWS_SESSION_TOKEN = "your-session-token"
   ```

2. **Keep config.json minimal**:
   ```json
   {
     "aws_region": "us-east-1"
   }
   ```

### **Option 3: Direct Credentials in config.json (Not Recommended for Production)**

⚠️ **Security Warning**: Only use this for testing. Never commit credentials to version control.

```json
{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "your-secret-key",
  "aws_region": "us-east-1"
}
```

### **Option 4: IAM Role Assumption**

For cross-account access or enhanced security:

```json
{
  "aws_assume_role_arn": "arn:aws:iam::123456789012:role/TerraformDriftDetectionRole",
  "aws_region": "us-east-1"
}
```

---

## 🌍 **Step 3: Configure Scanning Regions**

Update the regions you want to scan:

```json
{
  "scan_regions": [
    "us-east-1",
    "us-west-2",
    "eu-west-1"
  ]
}
```

---

## 🔒 **Required AWS Permissions**

Your AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-terraform-state-bucket",
        "arn:aws:s3:::your-terraform-state-bucket/*"
      ]
    },
    {
      "Effect": "Allow", 
      "Action": [
        "ec2:Describe*",
        "s3:List*",
        "s3:Get*",
        "rds:Describe*",
        "lambda:List*",
        "lambda:Get*",
        "iam:List*",
        "iam:Get*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📝 **Complete Example Configuration**

Here's a complete `config.json` example:

```json
{
  "debug": false,
  "port": 5000,
  
  "aws_profile": "production",
  "aws_region": "us-east-1",
  
  "terraform_s3_bucket": "mycompany-terraform-state",
  "terraform_s3_key": "production/infrastructure/terraform.tfstate",
  "terraform_s3_region": "us-east-1",
  
  "scan_interval_minutes": 5,
  "scan_regions": ["us-east-1", "us-west-2"],
  "enable_auto_scan": true,
  
  "enable_email_alerts": true,
  "email_from": "drift-alerts@mycompany.com",
  "email_to": ["devops@mycompany.com"],
  
  "severity_thresholds": {
    "CRITICAL": ["missing", "extra"],
    "HIGH": ["configuration"],
    "MEDIUM": ["tags"],
    "LOW": ["metadata"]
  }
}
```

---

## 🚀 **Testing Your Configuration**

1. **Update your config.json** with your actual AWS settings
2. **Restart the application**:
   ```powershell
   python start_enhanced_app.py
   ```
3. **Check the logs** for successful AWS connection
4. **Trigger a manual scan** via the web interface

---

## 🐛 **Troubleshooting**

### Common Issues:

1. **"Unable to locate credentials"**
   - Check your AWS profile/environment variables
   - Verify AWS CLI is configured: `aws sts get-caller-identity`

2. **"Access Denied" to S3**
   - Verify bucket name and path in config.json
   - Check S3 bucket permissions

3. **"Access Denied" for AWS resources**
   - Review the required permissions listed above
   - Test with: `aws ec2 describe-instances`

4. **Region mismatch**
   - Ensure `terraform_s3_region` matches your S3 bucket region
   - Verify `aws_region` and `scan_regions` are correct

---

## 🔄 **Switching from Demo to Production Mode**

Once configured, the app will automatically switch from demo mode to production mode when it detects valid AWS credentials and S3 configuration.

You'll see in the logs:
```
Mode: Production
AWS Integration: Enabled
Using real Terraform state data
Using real AWS resource data
```

Instead of:
```
Mode: Demo
AWS Integration: Disabled
Using mock Terraform state data
Using mock AWS resource data
```
