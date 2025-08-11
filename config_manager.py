"""
Configuration Management for AWS Terraform Drift Detection
Handles secure configuration with Azure Key Vault integration
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Application configuration settings"""
    # Application settings
    debug: bool = False
    secret_key: str = "change-me-in-production"
    port: int = 5000
    host: str = "0.0.0.0"
    
    # AWS settings
    aws_region: str = "us-east-1"
    aws_profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    aws_assume_role_arn: Optional[str] = None
    
    # Terraform S3 backend settings
    terraform_s3_bucket: Optional[str] = None
    terraform_s3_key: Optional[str] = None
    terraform_s3_region: Optional[str] = None
    
    # Scanning settings
    scan_interval_minutes: int = 5
    scan_regions: list = None
    enable_auto_scan: bool = True
    
    # Storage settings
    data_dir: str = "data"
    max_scan_history: int = 100
    max_alert_history: int = 500
    
    # Alert settings
    enable_email_alerts: bool = False
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: list = None
    
    # Webhook settings
    enable_webhook_alerts: bool = False
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Drift detection settings
    severity_thresholds: Dict[str, list] = None
    ignore_tags: list = None
    ignore_resources: list = None
    
    # Azure Key Vault settings (for production)
    azure_keyvault_url: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values for complex types"""
        if self.scan_regions is None:
            self.scan_regions = [self.aws_region]
            
        if self.email_to is None:
            self.email_to = []
            
        if self.severity_thresholds is None:
            self.severity_thresholds = {
                "CRITICAL": ["missing", "extra"],
                "HIGH": ["configuration"],
                "MEDIUM": ["tags"],
                "LOW": ["metadata"]
            }
            
        if self.ignore_tags is None:
            self.ignore_tags = ["LastModified", "CreatedBy"]
            
        if self.ignore_resources is None:
            self.ignore_resources = []

class ConfigManager:
    """Manages application configuration with multiple sources"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.json"
        self.config = AppConfig()
        
    def load_config(self) -> AppConfig:
        """Load configuration from multiple sources in priority order"""
        # 1. Load from file (if exists)
        self._load_from_file()
        
        # 2. Override with environment variables
        self._load_from_environment()
        
        # 3. Load secrets from Azure Key Vault (if configured)
        if self.config.azure_keyvault_url:
            self._load_from_azure_keyvault()
            
        # 4. Validate configuration
        self._validate_config()
        
        return self.config
        
    def save_config(self, config: AppConfig) -> None:
        """Save configuration to file (excluding secrets)"""
        safe_config = self._get_safe_config(config)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(safe_config, f, indent=2, default=str)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
            
    def _load_from_file(self) -> None:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_file):
            logger.info(f"Configuration file {self.config_file} not found, using defaults")
            return
            
        try:
            with open(self.config_file, 'r') as f:
                file_config = json.load(f)
                
            # Update config with file values
            for key, value in file_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    
            logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
            # Continue with defaults
            
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            # Application settings
            'DEBUG': ('debug', lambda x: x.lower() == 'true'),
            'SECRET_KEY': ('secret_key', str),
            'PORT': ('port', int),
            'HOST': ('host', str),
            
            # AWS settings
            'AWS_DEFAULT_REGION': ('aws_region', str),
            'AWS_PROFILE': ('aws_profile', str),
            'AWS_ACCESS_KEY_ID': ('aws_access_key_id', str),
            'AWS_SECRET_ACCESS_KEY': ('aws_secret_access_key', str),
            'AWS_SESSION_TOKEN': ('aws_session_token', str),
            'AWS_ASSUME_ROLE_ARN': ('aws_assume_role_arn', str),
            
            # Terraform settings
            'TERRAFORM_S3_BUCKET': ('terraform_s3_bucket', str),
            'TERRAFORM_S3_KEY': ('terraform_s3_key', str),
            'TERRAFORM_S3_REGION': ('terraform_s3_region', str),
            
            # Scanning settings
            'SCAN_INTERVAL_MINUTES': ('scan_interval_minutes', int),
            'SCAN_REGIONS': ('scan_regions', lambda x: x.split(',')),
            'ENABLE_AUTO_SCAN': ('enable_auto_scan', lambda x: x.lower() == 'true'),
            
            # Alert settings
            'ENABLE_EMAIL_ALERTS': ('enable_email_alerts', lambda x: x.lower() == 'true'),
            'EMAIL_SMTP_SERVER': ('email_smtp_server', str),
            'EMAIL_SMTP_PORT': ('email_smtp_port', int),
            'EMAIL_USERNAME': ('email_username', str),
            'EMAIL_PASSWORD': ('email_password', str),
            'EMAIL_FROM': ('email_from', str),
            'EMAIL_TO': ('email_to', lambda x: x.split(',')),
            
            'ENABLE_WEBHOOK_ALERTS': ('enable_webhook_alerts', lambda x: x.lower() == 'true'),
            'WEBHOOK_URL': ('webhook_url', str),
            'WEBHOOK_SECRET': ('webhook_secret', str),
            
            # Azure Key Vault settings
            'AZURE_KEYVAULT_URL': ('azure_keyvault_url', str),
            'AZURE_TENANT_ID': ('azure_tenant_id', str),
            'AZURE_CLIENT_ID': ('azure_client_id', str),
            'AZURE_CLIENT_SECRET': ('azure_client_secret', str),
        }
        
        for env_var, (config_attr, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = converter(value)
                    setattr(self.config, config_attr, converted_value)
                    logger.debug(f"Set {config_attr} from environment variable {env_var}")
                except Exception as e:
                    logger.warning(f"Error converting environment variable {env_var}: {e}")
                    
    def _load_from_azure_keyvault(self) -> None:
        """Load secrets from Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential, ClientSecretCredential
            
            # Choose authentication method
            if self.config.azure_client_id and self.config.azure_client_secret:
                credential = ClientSecretCredential(
                    tenant_id=self.config.azure_tenant_id,
                    client_id=self.config.azure_client_id,
                    client_secret=self.config.azure_client_secret
                )
            else:
                credential = DefaultAzureCredential()
                
            client = SecretClient(
                vault_url=self.config.azure_keyvault_url,
                credential=credential
            )
            
            # Map of secret names to config attributes
            secret_mappings = {
                'aws-access-key-id': 'aws_access_key_id',
                'aws-secret-access-key': 'aws_secret_access_key',
                'aws-session-token': 'aws_session_token',
                'terraform-s3-bucket': 'terraform_s3_bucket',
                'terraform-s3-key': 'terraform_s3_key',
                'email-password': 'email_password',
                'webhook-secret': 'webhook_secret',
                'app-secret-key': 'secret_key'
            }
            
            for secret_name, config_attr in secret_mappings.items():
                try:
                    secret = client.get_secret(secret_name)
                    setattr(self.config, config_attr, secret.value)
                    logger.debug(f"Loaded {config_attr} from Azure Key Vault")
                except Exception as e:
                    logger.debug(f"Secret {secret_name} not found in Key Vault: {e}")
                    
            logger.info("Azure Key Vault secrets loaded successfully")
            
        except ImportError:
            logger.warning("Azure SDK not available for Key Vault integration")
        except Exception as e:
            logger.error(f"Error loading secrets from Azure Key Vault: {e}")
            
    def _validate_config(self) -> None:
        """Validate configuration and log warnings for missing required settings"""
        warnings = []
        
        # Check AWS configuration
        if not self.config.aws_access_key_id and not self.config.aws_profile and not self.config.aws_assume_role_arn:
            warnings.append("No AWS authentication configured (access key, profile, or assume role)")
            
        # Check Terraform S3 backend
        if not self.config.terraform_s3_bucket:
            warnings.append("Terraform S3 bucket not configured - real state file access will not work")
            
        if not self.config.terraform_s3_key:
            warnings.append("Terraform S3 key not configured - real state file access will not work")
            
        # Check alert configuration
        if self.config.enable_email_alerts:
            if not self.config.email_smtp_server or not self.config.email_from or not self.config.email_to:
                warnings.append("Email alerts enabled but SMTP configuration incomplete")
                
        if self.config.enable_webhook_alerts and not self.config.webhook_url:
            warnings.append("Webhook alerts enabled but webhook URL not configured")
            
        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
            
    def _get_safe_config(self, config: AppConfig) -> Dict[str, Any]:
        """Get configuration dict with sensitive values masked"""
        config_dict = asdict(config)
        
        # Mask sensitive fields
        sensitive_fields = [
            'secret_key', 'aws_access_key_id', 'aws_secret_access_key', 
            'aws_session_token', 'email_password', 'webhook_secret',
            'azure_client_secret'
        ]
        
        for field in sensitive_fields:
            if field in config_dict and config_dict[field]:
                config_dict[field] = "***MASKED***"
                
        return config_dict
        
    def get_aws_config(self):
        """Get AWS-specific configuration"""
        from aws_integration import AWSConfig
        
        return AWSConfig(
            region=self.config.aws_region,
            profile=self.config.aws_profile,
            access_key_id=self.config.aws_access_key_id,
            secret_access_key=self.config.aws_secret_access_key,
            session_token=self.config.aws_session_token,
            s3_bucket=self.config.terraform_s3_bucket,
            s3_state_key=self.config.terraform_s3_key,
            assume_role_arn=self.config.aws_assume_role_arn
        )

def create_sample_config() -> None:
    """Create a sample configuration file"""
    sample_config = {
        "debug": False,
        "port": 5000,
        "host": "0.0.0.0",
        "aws_region": "us-east-1",
        "scan_interval_minutes": 5,
        "scan_regions": ["us-east-1", "us-west-2"],
        "enable_auto_scan": True,
        "max_scan_history": 100,
        "max_alert_history": 500,
        "enable_email_alerts": False,
        "email_smtp_server": "smtp.gmail.com",
        "email_smtp_port": 587,
        "email_from": "your-app@company.com",
        "email_to": ["admin@company.com"],
        "enable_webhook_alerts": False,
        "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "severity_thresholds": {
            "CRITICAL": ["missing", "extra"],
            "HIGH": ["configuration"],
            "MEDIUM": ["tags"],
            "LOW": ["metadata"]
        },
        "ignore_tags": ["LastModified", "CreatedBy"],
        "ignore_resources": []
    }
    
    with open("config.sample.json", 'w') as f:
        json.dump(sample_config, f, indent=2)
        
    print("Sample configuration created in config.sample.json")
    print("\nTo use:")
    print("1. Copy config.sample.json to config.json")
    print("2. Update the values for your environment")
    print("3. Set sensitive values via environment variables or Azure Key Vault")

if __name__ == "__main__":
    create_sample_config()
