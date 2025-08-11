# AWS Integration Setup Guide

This guide walks you through setting up real AWS integration for the Terraform Drift Detection application.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Authentication Setup](#aws-authentication-setup)
3. [Configuration Methods](#configuration-methods)
4. [Azure Key Vault Integration](#azure-key-vault-integration)
5. [Testing the Setup](#testing-the-setup)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform S3 Backend** configured with your state files
3. **Azure App Service** (for production deployment)
4. **Python 3.8+** with required packages installed

## AWS Authentication Setup

### Option 1: IAM Access Keys (Development/Testing)

1. **Create IAM User:**
   ```bash
   # Create a dedicated user for the drift detection app
   aws iam create-user --user-name drift-detection-app
   ```

2. **Attach Required Policies:**
   ```bash
   # Read-only access to AWS resources
   aws iam attach-user-policy \
     --user-name drift-detection-app \
     --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
   
   # S3 access for Terraform state files
   aws iam attach-user-policy \
     --user-name drift-detection-app \
     --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
   ```

3. **Create Access Keys:**
   ```bash
   aws iam create-access-key --user-name drift-detection-app
   ```

4. **Save the credentials securely** (use environment variables or Azure Key Vault)

### Option 2: Cross-Account IAM Role (Production Recommended)

1. **Create IAM Role in AWS:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::YOUR-AZURE-ACCOUNT:root"
         },
         "Action": "sts:AssumeRole",
         "Condition": {
           "StringEquals": {
             "sts:ExternalId": "your-unique-external-id"
           }
         }
       }
     ]
   }
   ```

2. **Attach Required Policies to the Role:**
   - `ReadOnlyAccess`
   - `AmazonS3ReadOnlyAccess`

3. **Configure Azure Managed Identity** to assume the AWS role

### Option 3: AWS Profile (Local Development)

1. **Configure AWS CLI:**
   ```bash
   aws configure --profile drift-detection
   ```

2. **Set profile in environment:**
   ```bash
   export AWS_PROFILE=drift-detection
   ```

## Configuration Methods

### Method 1: Environment Variables

Set these environment variables in your Azure App Service or local development environment:

```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
# AWS_SESSION_TOKEN=your-session-token  # Only if using temporary credentials
# AWS_ASSUME_ROLE_ARN=arn:aws:iam::123456789012:role/DriftDetectionRole  # For assume role

# Terraform S3 Backend
TERRAFORM_S3_BUCKET=your-terraform-state-bucket
TERRAFORM_S3_KEY=path/to/your/terraform.tfstate
TERRAFORM_S3_REGION=us-east-1

# Application Configuration
SCAN_INTERVAL_MINUTES=5
SCAN_REGIONS=us-east-1,us-west-2,eu-west-1
ENABLE_AUTO_SCAN=true

# Alert Configuration
ENABLE_EMAIL_ALERTS=false
ENABLE_WEBHOOK_ALERTS=false
# WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Azure Key Vault (Optional)
# AZURE_KEYVAULT_URL=https://your-keyvault.vault.azure.net/
# AZURE_TENANT_ID=your-tenant-id
# AZURE_CLIENT_ID=your-client-id
# AZURE_CLIENT_SECRET=your-client-secret
```

### Method 2: Configuration File

1. **Copy the sample configuration:**
   ```bash
   cp config.sample.json config.json
   ```

2. **Edit config.json:**
   ```json
   {
     "debug": false,
     "port": 5000,
     "host": "0.0.0.0",
     "aws_region": "us-east-1",
     "scan_interval_minutes": 5,
     "scan_regions": ["us-east-1", "us-west-2"],
     "enable_auto_scan": true,
     "terraform_s3_bucket": "your-terraform-state-bucket",
     "terraform_s3_key": "path/to/your/terraform.tfstate"
   }
   ```

3. **Note:** Never put sensitive credentials in the config file. Use environment variables or Azure Key Vault.

## Azure Key Vault Integration

For production deployments, use Azure Key Vault to store sensitive AWS credentials.

### 1. Create Azure Key Vault

```bash
# Create resource group
az group create --name rg-drift-detection --location eastus

# Create Key Vault
az keyvault create \
  --name kv-drift-detection-unique \
  --resource-group rg-drift-detection \
  --location eastus
```

### 2. Store AWS Credentials

```bash
# Store AWS credentials
az keyvault secret set --vault-name kv-drift-detection-unique --name "aws-access-key-id" --value "your-access-key-id"
az keyvault secret set --vault-name kv-drift-detection-unique --name "aws-secret-access-key" --value "your-secret-access-key"
az keyvault secret set --vault-name kv-drift-detection-unique --name "terraform-s3-bucket" --value "your-terraform-state-bucket"
az keyvault secret set --vault-name kv-drift-detection-unique --name "terraform-s3-key" --value "path/to/your/terraform.tfstate"
az keyvault secret set --vault-name kv-drift-detection-unique --name "app-secret-key" --value "your-flask-secret-key"
```

### 3. Configure App Service Managed Identity

```bash
# Enable system-assigned managed identity for App Service
az webapp identity assign --name your-app-name --resource-group rg-drift-detection

# Grant access to Key Vault
az keyvault set-policy \
  --name kv-drift-detection-unique \
  --object-id $(az webapp identity show --name your-app-name --resource-group rg-drift-detection --query principalId -o tsv) \
  --secret-permissions get list
```

### 4. Configure Environment Variables

Set these in your App Service:

```bash
AZURE_KEYVAULT_URL=https://kv-drift-detection-unique.vault.azure.net/
```

## Testing the Setup

### 1. Test AWS Connection

```python
# Run this to test AWS connection
python -c "
from aws_integration import AWSIntegration
from config_manager import ConfigManager

config_manager = ConfigManager()
aws_config = config_manager.get_aws_config()
aws_integration = AWSIntegration(aws_config)

result = aws_integration.test_connection()
print('AWS Connection Test:', result)
"
```

### 2. Test Terraform State Access

```python
# Test S3 state file access
python -c "
from aws_integration import AWSIntegration
from config_manager import ConfigManager

config_manager = ConfigManager()
aws_config = config_manager.get_aws_config()
aws_integration = AWSIntegration(aws_config)

try:
    state = aws_integration.get_terraform_state()
    print('Terraform State Access: SUCCESS')
    print(f'State version: {state.get(\"version\")}')
    print(f'Resources: {len(state.get(\"resources\", []))}')
except Exception as e:
    print(f'Terraform State Access: FAILED - {e}')
"
```

### 3. Test Resource Scanning

```python
# Test AWS resource scanning
python -c "
from aws_integration import AWSIntegration
from config_manager import ConfigManager

config_manager = ConfigManager()
aws_config = config_manager.get_aws_config()
aws_integration = AWSIntegration(aws_config)

try:
    resources = aws_integration.scan_aws_resources(['us-east-1'])
    print('AWS Resource Scanning: SUCCESS')
    for region, data in resources.items():
        if isinstance(data, dict):
            total = sum(len(v) for v in data.values() if isinstance(v, list))
            print(f'Region {region}: {total} resources')
except Exception as e:
    print(f'AWS Resource Scanning: FAILED - {e}')
"
```

### 4. Run Complete Drift Detection

```bash
# Start the enhanced application
python drift_app_enhanced.py
```

Navigate to `http://localhost:5000` and trigger a manual scan to test the complete workflow.

## Troubleshooting

### Common Issues

1. **AWS Authentication Errors:**
   ```
   Error: "Unable to locate credentials"
   ```
   - Check environment variables
   - Verify AWS profile configuration
   - Ensure IAM permissions are correct

2. **S3 Access Denied:**
   ```
   Error: "Access denied to s3://bucket/key"
   ```
   - Verify S3 bucket name and key
   - Check IAM permissions for S3 access
   - Ensure bucket region matches configuration

3. **Azure Key Vault Access:**
   ```
   Error: "Forbidden" from Key Vault
   ```
   - Check managed identity configuration
   - Verify Key Vault access policies
   - Ensure correct Key Vault URL

4. **Resource Scanning Timeouts:**
   ```
   Error: "Read timeout"
   ```
   - Check network connectivity
   - Verify AWS service health
   - Consider reducing scan regions

### Debug Mode

Enable debug logging by setting:

```bash
DEBUG=true
```

Or in config.json:
```json
{
  "debug": true
}
```

### Log Analysis

Check application logs for detailed error information:

```bash
# View logs in Azure App Service
az webapp log tail --name your-app-name --resource-group rg-drift-detection

# Or download logs
az webapp log download --name your-app-name --resource-group rg-drift-detection
```

## Security Best Practices

1. **Never hardcode credentials** in source code
2. **Use Azure Key Vault** for production deployments
3. **Apply least privilege** IAM policies
4. **Rotate credentials regularly**
5. **Monitor access logs** for unusual activity
6. **Use VPC endpoints** for S3 access when possible
7. **Enable CloudTrail** for audit logging

## Performance Optimization

1. **Limit scan regions** to only necessary regions
2. **Adjust scan frequency** based on change rate
3. **Use resource filtering** to exclude non-managed resources
4. **Implement caching** for frequently accessed data
5. **Monitor resource usage** and costs

## Support

For issues with this integration:

1. Check the application logs
2. Verify AWS permissions and configuration
3. Test individual components (auth, S3, scanning)
4. Review the troubleshooting section
5. Check AWS service health status

## Next Steps

Once AWS integration is working:

1. **Configure alerting** (email/webhook notifications)
2. **Set up monitoring** and dashboards
3. **Implement CI/CD** for automatic deployments
4. **Add custom drift rules** based on your environment
5. **Scale for multiple environments** (dev/staging/prod)
