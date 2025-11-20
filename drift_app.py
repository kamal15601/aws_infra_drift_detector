"""
AWS Terraform Drift Detection Web Application
Enhanced Version with Real AWS Integration + Demo Mode

This application provides:
- Real AWS resource scanning using boto3
- Real Terraform state file access from S3
- Mock data mode for demonstrations
- Real-time drift detection
- Alert processing and notifications
- Dashboard with live updates
- Secure credential management
"""

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
import json
import os
from datetime import datetime, timedelta
import threading
import time
import random
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import uuid

# Import new modules
from config_manager import ConfigManager, AppConfig
from aws_integration import AWSIntegration, AWSConfig
from drift_engine import DriftDetectionEngine, DriftItem

# Setup Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
config_manager = ConfigManager()
app_config = config_manager.load_config()
app.secret_key = app_config.secret_key

# AWS Integration (will be None if not configured)
aws_integration = None
try:
    aws_config = config_manager.get_aws_config()
    aws_integration = AWSIntegration(aws_config)
    connection_test = aws_integration.test_connection()
    if connection_test['success']:
        logger.info(f"AWS connection successful: {connection_test['user_arn']}")
    else:
        logger.warning(f"AWS connection failed: {connection_test['error']}")
        aws_integration = None
except Exception as e:
    logger.warning(f"AWS integration not available: {e}")
    aws_integration = None

# Drift detection engine
drift_engine = DriftDetectionEngine(asdict(app_config))

# Create data directories
os.makedirs(app_config.data_dir, exist_ok=True)
os.makedirs(f'{app_config.data_dir}/scans', exist_ok=True)
os.makedirs(f'{app_config.data_dir}/alerts', exist_ok=True)
os.makedirs(f'{app_config.data_dir}/mock', exist_ok=True)

# Global variables
current_scan_id = None
demo_mode = aws_integration is None  # Auto-detect demo mode
auto_scanner_running = False

# Alert processor
class AlertProcessor:
    """Processes and manages alerts from drift detection"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    def process_drift_items(self, drift_items: List[DriftItem]) -> List[Dict[str, Any]]:
        """Process drift items and create alerts"""
        alerts = []
        
        for drift_item in drift_items:
            alert = {
                'alert_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'severity': drift_item.severity,
                'status': 'NEW',
                'resource': {
                    'type': drift_item.resource_type,
                    'name': drift_item.resource_name,
                    'terraform_address': drift_item.terraform_address,
                    'aws_id': drift_item.aws_id,
                    'region': drift_item.region
                },
                'drift_details': {
                    'drift_type': drift_item.drift_type,
                    'differences': drift_item.differences,
                    'first_detected': drift_item.first_detected,
                    'last_seen': drift_item.last_seen
                },
                'alert_metadata': {
                    'environment': drift_item.environment,
                    'scan_id': current_scan_id,
                    'created_by': 'drift-detection-system'
                }
            }
            
            alerts.append(alert)
            
        # Save alerts to file
        if alerts:
            self._save_alerts(alerts)
            
        # Send notifications if configured
        if self.config.enable_email_alerts:
            self._send_email_notifications(alerts)
            
        if self.config.enable_webhook_alerts:
            self._send_webhook_notifications(alerts)
            
        return alerts
        
    def _save_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Save alerts to local storage"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{app_config.data_dir}/alerts/alerts_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(alerts, f, indent=2)
            logger.info(f"Saved {len(alerts)} alerts to {filename}")
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
            
    def _send_email_notifications(self, alerts: List[Dict[str, Any]]) -> None:
        """Send email notifications for high-severity alerts"""
        high_severity_alerts = [a for a in alerts if a['severity'] in ['CRITICAL', 'HIGH']]
        
        if not high_severity_alerts:
            return
            
        # TODO: Implement email sending
        logger.info(f"Would send email notifications for {len(high_severity_alerts)} high-severity alerts")
        
    def _send_webhook_notifications(self, alerts: List[Dict[str, Any]]) -> None:
        """Send webhook notifications for alerts"""
        if not self.config.webhook_url:
            return
            
        # TODO: Implement webhook sending
        logger.info(f"Would send webhook notifications for {len(alerts)} alerts")

alert_processor = AlertProcessor(app_config)

class MockDataGenerator:
    """Generates realistic mock data for demonstration"""
    
    def __init__(self):
        self.environments = ['production', 'staging', 'development']
        self.aws_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        self.resource_types = [
            'aws_instance', 'aws_security_group', 'aws_s3_bucket', 
            'aws_rds_instance', 'aws_iam_role', 'aws_vpc', 
            'aws_subnet', 'aws_load_balancer', 'aws_lambda_function'
        ]
        
    def generate_terraform_state(self) -> Dict[str, Any]:
        """Generate mock Terraform state file data"""
        return {
            "version": 4,
            "terraform_version": "1.5.0",
            "serial": 123,
            "lineage": str(uuid.uuid4()),
            "outputs": {},
            "resources": [
                {
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web_server",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 1,
                            "attributes": {
                                "id": "i-1234567890abcdef0",
                                "instance_type": "t3.medium",
                                "ami": "ami-0c55b159cbfafe1d0",
                                "availability_zone": "us-east-1a",
                                "security_groups": ["sg-web-server"],
                                "tags": {
                                    "Name": "web-server-prod",
                                    "Environment": "production",
                                    "ManagedBy": "terraform"
                                },
                                "public_ip": "52.1.2.3",
                                "private_ip": "10.0.1.10"
                            }
                        }
                    ]
                },
                {
                    "mode": "managed",
                    "type": "aws_security_group",
                    "name": "web_sg",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 1,
                            "attributes": {
                                "id": "sg-web-server",
                                "name": "web-server-sg",
                                "description": "Security group for web server",
                                "ingress": [
                                    {
                                        "from_port": 80,
                                        "to_port": 80,
                                        "protocol": "tcp",
                                        "cidr_blocks": ["0.0.0.0/0"]
                                    },
                                    {
                                        "from_port": 443,
                                        "to_port": 443,
                                        "protocol": "tcp",
                                        "cidr_blocks": ["0.0.0.0/0"]
                                    }
                                ],
                                "tags": {
                                    "Name": "web-server-sg",
                                    "Environment": "production"
                                }
                            }
                        }
                    ]
                },
                {
                    "mode": "managed",
                    "type": "aws_s3_bucket",
                    "name": "app_data",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 0,
                            "attributes": {
                                "id": "my-app-data-bucket-prod",
                                "bucket": "my-app-data-bucket-prod",
                                "versioning": [{"enabled": True}],
                                "server_side_encryption_configuration": [
                                    {
                                        "rule": [
                                            {
                                                "apply_server_side_encryption_by_default": [
                                                    {"sse_algorithm": "AES256"}
                                                ]
                                            }
                                        ]
                                    }
                                ],
                                "tags": {
                                    "Name": "app-data-bucket",
                                    "Environment": "production",
                                    "BackupRetention": "30-days"
                                }
                            }
                        }
                    ]
                }
            ]
        }

class DriftScanner:
    """Main drift scanner class that orchestrates the scanning process"""
    
    def __init__(self, config: AppConfig, aws_integration: Optional[AWSIntegration], demo_mode: bool = False):
        self.config = config
        self.aws_integration = aws_integration
        self.demo_mode = demo_mode
        
        if demo_mode:
            self.mock_generator = MockDataGenerator()
            
    def perform_scan(self) -> Dict[str, Any]:
        """Perform a complete drift detection scan"""
        global current_scan_id
        current_scan_id = str(uuid.uuid4())
        
        scan_start = datetime.now()
        logger.info(f"Starting drift scan {current_scan_id}")
        
        try:
            # Get Terraform state
            if self.demo_mode:
                terraform_state = self.mock_generator.generate_terraform_state()
                logger.info("Using mock Terraform state data")
            else:
                terraform_state = self.aws_integration.get_terraform_state()
                logger.info("Retrieved Terraform state from S3")
                
            # Get AWS resources
            if self.demo_mode:
                aws_resources = {'us-east-1': self.mock_generator.generate_aws_resources(with_drift=True)}
                logger.info("Using mock AWS resource data")
            else:
                aws_resources = self.aws_integration.scan_aws_resources(self.config.scan_regions)
                logger.info(f"Scanned AWS resources in regions: {self.config.scan_regions}")
                
            # Detect drift
            drift_items = drift_engine.detect_drift(terraform_state, aws_resources)
            
            # Process alerts
            alerts = alert_processor.process_drift_items(drift_items)
            
            # Prepare scan results
            scan_results = {
                'scan_id': current_scan_id,
                'timestamp': scan_start.isoformat(),
                'duration_seconds': (datetime.now() - scan_start).total_seconds(),
                'mode': 'demo' if self.demo_mode else 'production',
                'terraform_state': {
                    'version': terraform_state.get('version', 'unknown'),
                    'serial': terraform_state.get('serial', 0),
                    'resource_count': len(terraform_state.get('resources', []))
                },
                'aws_resources': {
                    'regions_scanned': list(aws_resources.keys()) if isinstance(aws_resources, dict) else [],
                    'total_resources': self._count_aws_resources(aws_resources)
                },
                'drift_summary': {
                    'total_drift_items': len(drift_items),
                    'by_severity': self._count_by_severity(drift_items),
                    'by_type': self._count_by_type(drift_items),
                    'by_resource_type': self._count_by_resource_type(drift_items)
                },
                'alerts_generated': len(alerts),
                'drift_items': [item.to_dict() for item in drift_items]
            }
            
            # Save scan results
            self._save_scan_results(scan_results)
            
            logger.info(f"Scan {current_scan_id} completed. Found {len(drift_items)} drift items, generated {len(alerts)} alerts")
            return scan_results
            
        except Exception as e:
            logger.error(f"Error during drift scan: {e}")
            return {
                'scan_id': current_scan_id,
                'timestamp': scan_start.isoformat(),
                'error': str(e),
                'mode': 'demo' if self.demo_mode else 'production'
            }
            
    def _count_aws_resources(self, aws_resources: Dict) -> int:
        """Count total AWS resources across all regions"""
        total = 0
        for region_data in aws_resources.values():
            if isinstance(region_data, dict):
                for resource_type, resources in region_data.items():
                    if isinstance(resources, list):
                        total += len(resources)
        return total
        
    def _count_by_severity(self, drift_items: List[DriftItem]) -> Dict[str, int]:
        """Count drift items by severity"""
        counts = {}
        for item in drift_items:
            counts[item.severity] = counts.get(item.severity, 0) + 1
        return counts
        
    def _count_by_type(self, drift_items: List[DriftItem]) -> Dict[str, int]:
        """Count drift items by drift type"""
        counts = {}
        for item in drift_items:
            counts[item.drift_type] = counts.get(item.drift_type, 0) + 1
        return counts
        
    def _count_by_resource_type(self, drift_items: List[DriftItem]) -> Dict[str, int]:
        """Count drift items by resource type"""
        counts = {}
        for item in drift_items:
            counts[item.resource_type] = counts.get(item.resource_type, 0) + 1
        return counts
        
    def _save_scan_results(self, scan_results: Dict[str, Any]) -> None:
        """Save scan results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{app_config.data_dir}/scans/scan_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(scan_results, f, indent=2)
                
            # Also save as latest scan
            latest_filename = f"{app_config.data_dir}/latest_scan.json"
            with open(latest_filename, 'w') as f:
                json.dump(scan_results, f, indent=2)
                
            logger.info(f"Saved scan results to {filename}")
        except Exception as e:
            logger.error(f"Error saving scan results: {e}")

# Initialize scanner
scanner = DriftScanner(app_config, aws_integration, demo_mode)
    """Generates realistic mock data for demonstration"""
    
    def __init__(self):
        self.environments = ['production', 'staging', 'development']
        self.aws_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        self.resource_types = [
            'aws_instance', 'aws_security_group', 'aws_s3_bucket', 
            'aws_rds_instance', 'aws_iam_role', 'aws_vpc', 
            'aws_subnet', 'aws_load_balancer', 'aws_lambda_function'
        ]
        
    def generate_terraform_state(self) -> Dict[str, Any]:
        """Generate mock Terraform state file data"""
        return {
            "version": 4,
            "terraform_version": "1.5.0",
            "serial": 123,
            "lineage": str(uuid.uuid4()),
            "outputs": {},
            "resources": [
                {
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web_server",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 1,
                            "attributes": {
                                "id": "i-1234567890abcdef0",
                                "instance_type": "t3.medium",
                                "ami": "ami-0c55b159cbfafe1d0",
                                "availability_zone": "us-east-1a",
                                "security_groups": ["sg-web-server"],
                                "tags": {
                                    "Name": "web-server-prod",
                                    "Environment": "production",
                                    "ManagedBy": "terraform"
                                },
                                "public_ip": "52.1.2.3",
                                "private_ip": "10.0.1.10"
                            }
                        }
                    ]
                },
                {
                    "mode": "managed",
                    "type": "aws_security_group",
                    "name": "web_sg",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 1,
                            "attributes": {
                                "id": "sg-web-server",
                                "name": "web-server-sg",
                                "description": "Security group for web server",
                                "ingress": [
                                    {
                                        "from_port": 80,
                                        "to_port": 80,
                                        "protocol": "tcp",
                                        "cidr_blocks": ["0.0.0.0/0"]
                                    },
                                    {
                                        "from_port": 443,
                                        "to_port": 443,
                                        "protocol": "tcp",
                                        "cidr_blocks": ["0.0.0.0/0"]
                                    }
                                ],
                                "tags": {
                                    "Name": "web-server-sg",
                                    "Environment": "production"
                                }
                            }
                        }
                    ]
                },
                {
                    "mode": "managed",
                    "type": "aws_s3_bucket",
                    "name": "app_data",
                    "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
                    "instances": [
                        {
                            "schema_version": 0,
                            "attributes": {
                                "id": "my-app-data-bucket-prod",
                                "bucket": "my-app-data-bucket-prod",
                                "versioning": [{"enabled": True}],
                                "server_side_encryption_configuration": [
                                    {
                                        "rule": [
                                            {
                                                "apply_server_side_encryption_by_default": [
                                                    {"sse_algorithm": "AES256"}
                                                ]
                                            }
                                        ]
                                    }
                                ],
                                "tags": {
                                    "Name": "app-data-bucket",
                                    "Environment": "production",
                                    "BackupRetention": "30-days"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    
    def generate_aws_resources(self, with_drift=True) -> Dict[str, Any]:
        """Generate mock AWS resource data (simulating AWS API responses)"""
        # Start with data matching Terraform state
        aws_data = {
            "ec2_instances": [
                {
                    "InstanceId": "i-1234567890abcdef0",
                    "InstanceType": "t3.large" if with_drift else "t3.medium",  # DRIFT: size changed
                    "ImageId": "ami-0c55b159cbfafe1d0",
                    "State": {"Name": "running"},
                    "Placement": {"AvailabilityZone": "us-east-1a"},
                    "SecurityGroups": [{"GroupId": "sg-web-server", "GroupName": "web-server-sg"}],
                    "Tags": [
                        {"Key": "Name", "Value": "web-server-prod"},
                        {"Key": "Environment", "Value": "production"},
                        {"Key": "ManagedBy", "Value": "terraform"},
                        {"Key": "Owner", "Value": "devops-team"} if with_drift else None  # DRIFT: new tag
                    ],
                    "PublicIpAddress": "52.1.2.3",
                    "PrivateIpAddress": "10.0.1.10"
                }
            ],
            "security_groups": [
                {
                    "GroupId": "sg-web-server",
                    "GroupName": "web-server-sg",
                    "Description": "Security group for web server",
                    "IpPermissions": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 80,
                            "ToPort": 80,
                            "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                        },
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 443,
                            "ToPort": 443,
                            "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                        }
                    ] + ([{  # DRIFT: new SSH rule added manually
                        "IpProtocol": "tcp",
                        "FromPort": 22,
                        "ToPort": 22,
                        "IpRanges": [{"CidrIp": "10.0.0.0/8"}]
                    }] if with_drift else []),
                    "Tags": [
                        {"Key": "Name", "Value": "web-server-sg"},
                        {"Key": "Environment", "Value": "production"}
                    ]
                }
            ],
            "s3_buckets": [
                {
                    "Name": "my-app-data-bucket-prod",
                    "CreationDate": "2024-01-15T10:30:00Z",
                    "Versioning": {"Status": "Enabled"},
                    "Encryption": {
                        "Rules": [
                            {
                                "ApplyServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": "aws:kms" if with_drift else "AES256"  # DRIFT: encryption changed
                                }
                            }
                        ]
                    },
                    "Tags": [
                        {"Key": "Name", "Value": "app-data-bucket"},
                        {"Key": "Environment", "Value": "production"}
                        # DRIFT: BackupRetention tag missing
                    ]
                }
            ]
        }
        
        if with_drift:
            # Add a manually created resource not in Terraform
            aws_data["ec2_instances"].append({
                "InstanceId": "i-9876543210fedcba0",
                "InstanceType": "t3.micro",
                "ImageId": "ami-0c55b159cbfafe1d0",
                "State": {"Name": "running"},
                "Placement": {"AvailabilityZone": "us-east-1b"},
                "Tags": [
                    {"Key": "Name", "Value": "manual-test-instance"},
                    {"Key": "Environment", "Value": "production"},
                    {"Key": "CreatedBy", "Value": "manual"}
                ],
                "PublicIpAddress": "52.1.2.100",
                "PrivateIpAddress": "10.0.1.100"
            })
        
        return aws_data
    
    def generate_drift_items(self) -> List[DriftItem]:
        """Generate realistic drift items"""
        now = datetime.now().isoformat()
        
        return [
            DriftItem(
                resource_type="aws_instance",
                resource_name="web-server-prod",
                terraform_address="aws_instance.web_server",
                aws_id="i-1234567890abcdef0",
                drift_type="configuration",
                severity="HIGH",
                differences={
                    "instance_type": {
                        "terraform": "t3.medium",
                        "aws": "t3.large",
                        "impact": "Cost increase, performance change"
                    },
                    "tags": {
                        "terraform": {"Name": "web-server-prod", "Environment": "production", "ManagedBy": "terraform"},
                        "aws": {"Name": "web-server-prod", "Environment": "production", "ManagedBy": "terraform", "Owner": "devops-team"},
                        "impact": "New tag added manually"
                    }
                },
                first_detected=now,
                last_seen=now
            ),
            DriftItem(
                resource_type="aws_security_group",
                resource_name="web-server-sg",
                terraform_address="aws_security_group.web_sg",
                aws_id="sg-web-server",
                drift_type="configuration",
                severity="CRITICAL",
                differences={
                    "ingress_rules": {
                        "terraform": "HTTP(80), HTTPS(443)",
                        "aws": "HTTP(80), HTTPS(443), SSH(22)",
                        "impact": "New SSH access rule added - potential security risk"
                    }
                },
                first_detected=now,
                last_seen=now
            ),
            DriftItem(
                resource_type="aws_s3_bucket",
                resource_name="app-data-bucket",
                terraform_address="aws_s3_bucket.app_data",
                aws_id="my-app-data-bucket-prod",
                drift_type="configuration",
                severity="MEDIUM",
                differences={
                    "encryption": {
                        "terraform": "AES256",
                        "aws": "aws:kms",
                        "impact": "Encryption method changed to KMS"
                    },
                    "tags": {
                        "terraform": {"BackupRetention": "30-days"},
                        "aws": "missing",
                        "impact": "Backup retention tag removed"
                    }
                },
                first_detected=now,
                last_seen=now
            ),
            DriftItem(
                resource_type="aws_instance",
                resource_name="manual-test-instance",
                terraform_address="NOT_IN_TERRAFORM",
                aws_id="i-9876543210fedcba0",
                drift_type="extra",
                severity="MEDIUM",
                differences={
                    "resource_existence": {
                        "terraform": "not_defined",
                        "aws": "exists",
                        "impact": "Manually created resource not managed by Terraform"
                    }
                },
                first_detected=now,
                last_seen=now
            )
        ]

# Initialize mock data generator
mock_generator = MockDataGenerator()

def save_data(filename: str, data: Any) -> None:
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")

def load_data(filename: str) -> Any:
    """Load data from JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error loading data from {filename}: {e}")
        return None

def simulate_drift_scan() -> Dict[str, Any]:
    """Simulate a complete drift detection scan"""
    global current_scan_id
    
    scan_id = f"scan_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    current_scan_id = scan_id
    
    logger.info(f"Starting simulated drift scan: {scan_id}")
    
    # Generate mock data
    terraform_state = mock_generator.generate_terraform_state()
    aws_resources = mock_generator.generate_aws_resources(with_drift=True)
    drift_items = mock_generator.generate_drift_items()
    
    # Create scan result
    scan_result = {
        "scan_id": scan_id,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "terraform_state": {
            "source": "s3://terraform-state-bucket/production/terraform.tfstate",
            "last_modified": (datetime.now() - timedelta(hours=2)).isoformat(),
            "version": terraform_state["version"],
            "resources_count": len(terraform_state["resources"])
        },
        "aws_scan": {
            "regions_scanned": ["us-east-1"],
            "resources_found": sum(len(v) if isinstance(v, list) else 1 for v in aws_resources.values()),
            "scan_duration_seconds": random.uniform(15.0, 45.0)
        },
        "drift_summary": {
            "total_resources_checked": 4,
            "drift_detected": len([d for d in drift_items if d.drift_type != 'none']),
            "by_severity": {
                "CRITICAL": len([d for d in drift_items if d.severity == 'CRITICAL']),
                "HIGH": len([d for d in drift_items if d.severity == 'HIGH']),
                "MEDIUM": len([d for d in drift_items if d.severity == 'MEDIUM']),
                "LOW": len([d for d in drift_items if d.severity == 'LOW'])
            },
            "by_type": {
                "configuration": len([d for d in drift_items if d.drift_type == 'configuration']),
                "missing": len([d for d in drift_items if d.drift_type == 'missing']),
                "extra": len([d for d in drift_items if d.drift_type == 'extra']),
                "tags": len([d for d in drift_items if d.drift_type == 'tags'])
            }
        },
        "drift_items": [asdict(item) for item in drift_items],
        "next_scan_scheduled": (datetime.now() + timedelta(minutes=5)).isoformat()
    }
    
    # Save scan result
    save_data(f"data/scans/{scan_id}.json", scan_result)
    save_data("data/latest_scan.json", scan_result)
    
    # Process alerts for new drift
    process_alerts(drift_items, scan_result)
    
    logger.info(f"Drift scan completed: {len(drift_items)} drift items detected")
    return scan_result

def process_alerts(drift_items: List[DriftItem], scan_result: Dict[str, Any]) -> None:
    """Process alerts for detected drift"""
    
    alerts = []
    now = datetime.now().isoformat()
    
    for drift in drift_items:
        if drift.drift_type != 'none':  # Only alert on actual drift
            alert = Alert(
                alert_id=f"alert_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{drift.aws_id}",
                timestamp=now,
                severity=drift.severity,
                status="NEW",
                resource={
                    "type": drift.resource_type,
                    "name": drift.resource_name,
                    "terraform_address": drift.terraform_address,
                    "aws_id": drift.aws_id
                },
                drift_details={
                    "drift_type": drift.drift_type,
                    "differences": drift.differences
                },
                alert_metadata={
                    "scan_id": scan_result["scan_id"],
                    "first_detected": drift.first_detected,
                    "last_seen": drift.last_seen,
                    "occurrence_count": 1,
                    "environment": drift.environment
                }
            )
            alerts.append(asdict(alert))
    
    # Save alerts
    if alerts:
        # Load existing alerts
        existing_alerts = load_data("data/alerts/active_alerts.json") or []
        
        # Add new alerts
        existing_alerts.extend(alerts)
        
        # Save updated alerts
        save_data("data/alerts/active_alerts.json", existing_alerts)
        
        logger.info(f"Generated {len(alerts)} new alerts")

def background_scanner():
    """Background thread that runs drift detection every 5 minutes"""
    global auto_scanner_running
    
    logger.info("Background scanner started - will run every 5 minutes")
    auto_scanner_running = True
    
    while auto_scanner_running:
        try:
            if demo_mode:
                # Run a scan
                scan_result = simulate_drift_scan()
                logger.info(f"Background scan completed: {scan_result['scan_id']}")
            
            # Wait 5 minutes (300 seconds)
            time.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in background scanner: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Load latest scan data
    latest_scan = load_data("data/latest_scan.json")
    active_alerts = load_data("data/alerts/active_alerts.json") or []
    
    # Generate some statistics
    stats = {
        "total_resources": latest_scan["drift_summary"]["total_resources_checked"] if latest_scan else 0,
        "drift_detected": latest_scan["drift_summary"]["drift_detected"] if latest_scan else 0,
        "active_alerts": len(active_alerts),
        "last_scan": latest_scan["timestamp"] if latest_scan else "Never",
        "next_scan": latest_scan["next_scan_scheduled"] if latest_scan else "Not scheduled",
        "scanner_status": "Running" if auto_scanner_running else "Stopped"
    }
    
    return render_template('dashboard.html', 
                         latest_scan=latest_scan, 
                         active_alerts=active_alerts[:5],  # Show only recent alerts
                         stats=stats)

@app.route('/api/scan/latest')
def api_latest_scan():
    """API endpoint for latest scan data"""
    latest_scan = load_data("data/latest_scan.json")
    return jsonify(latest_scan) if latest_scan else jsonify({"error": "No scan data available"})

@app.route('/api/alerts/active')
def api_active_alerts():
    """API endpoint for active alerts"""
    active_alerts = load_data("data/alerts/active_alerts.json") or []
    return jsonify(active_alerts)

@app.route('/api/scan/trigger', methods=['POST'])
def api_trigger_scan():
    """API endpoint to manually trigger a scan"""
    try:
        scan_result = simulate_drift_scan()
        return jsonify({"success": True, "scan_id": scan_result["scan_id"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/scan-results')
def scan_results():
    """Detailed scan results page"""
    latest_scan = load_data("data/latest_scan.json")
    return render_template('scan_results.html', scan_data=latest_scan)

@app.route('/alerts')
def alerts_page():
    """Alerts management page"""
    active_alerts = load_data("data/alerts/active_alerts.json") or []
    return render_template('alerts.html', alerts=active_alerts)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "demo_mode": demo_mode,
        "scanner_running": auto_scanner_running,
        "latest_scan": current_scan_id
    })

if __name__ == '__main__':
    # Initialize with some mock data
    logger.info("Starting AWS Terraform Drift Detection Demo")
    
    # Generate initial scan data
    simulate_drift_scan()
    
    # Start background scanner thread
    scanner_thread = threading.Thread(target=background_scanner, daemon=True)
    scanner_thread.start()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=8000, threaded=True)
