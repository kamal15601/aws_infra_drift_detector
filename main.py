"""
AWS Terraform Drift Detection Web Application.
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

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for, make_response
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
import pytz

# Import new modules
from config_manager import ConfigManager, AppConfig
from aws_integration import AWSIntegration, AWSConfig
from drift_engine import DriftDetectionEngine, DriftItem

# Setup Flask app
app = Flask(__name__)

# IST timezone formatting function
def format_timestamp_ist(timestamp_str):
    """Convert ISO timestamp to IST format: Date : Time (HH:MM AM/PM)"""
    try:
        # Handle special cases
        if timestamp_str in ["Never", "Unknown", "Not scheduled", None, ""]:
            return str(timestamp_str) if timestamp_str else "Never"
        
        # Parse the ISO timestamp
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = timestamp_str
        
        # Convert to IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            utc = pytz.timezone('UTC')
            dt = utc.localize(dt)
        
        ist_time = dt.astimezone(ist)
        
        # Format as: Date : Time (HH:MM AM/PM)
        formatted_date = ist_time.strftime('%Y-%m-%d')
        formatted_time = ist_time.strftime('%I:%M %p')
        
        return f"{formatted_date} : {formatted_time}"
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp_str}: {e}")
        return str(timestamp_str)

# Register template filter
@app.template_filter('ist_datetime')
def ist_datetime_filter(timestamp_str):
    return format_timestamp_ist(timestamp_str)

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
            ],
            "rds_instances": [],
            "lambda_functions": [],
            "iam_roles": [],
            "vpcs": [],
            "subnets": [],
            "load_balancers": []
        }
        
        # Filter out None values from tags
        for instance in aws_data["ec2_instances"]:
            instance["Tags"] = [tag for tag in instance["Tags"] if tag is not None]
        
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

# Background scanner thread
def auto_scanner():
    """Background thread that runs periodic scans"""
    global auto_scanner_running
    
    while auto_scanner_running:
        try:
            logger.info("Starting automated drift scan")
            scanner.perform_scan()
            
            # Wait for next scan
            wait_minutes = app_config.scan_interval_minutes
            logger.info(f"Next scan in {wait_minutes} minutes")
            time.sleep(wait_minutes * 60)
            
        except Exception as e:
            logger.error(f"Error in auto scanner: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

# Helper functions for data access
def load_latest_scan():
    """Load latest scan data"""
    try:
        latest_file = f"{app_config.data_dir}/latest_scan.json"
        if os.path.exists(latest_file):
            with open(latest_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading latest scan: {e}")
    return None

def load_active_alerts():
    """Load recent alerts"""
    try:
        alerts_dir = f"{app_config.data_dir}/alerts"
        all_alerts = []
        
        if os.path.exists(alerts_dir):
            for filename in os.listdir(alerts_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(alerts_dir, filename)
                    with open(filepath, 'r') as f:
                        alerts_data = json.load(f)
                        all_alerts.extend(alerts_data)
        
        # Sort by timestamp (newest first) and return recent ones
        all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_alerts[:50]  # Return up to 50 recent alerts
    except Exception as e:
        logger.error(f"Error loading alerts: {e}")
    return []

# Flask Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Load latest scan data
    latest_scan = load_latest_scan()
    active_alerts = load_active_alerts()
    
    # Determine current mode from scan data or AWS integration status
    current_mode = 'demo'
    if latest_scan and 'mode' in latest_scan:
        current_mode = latest_scan['mode']
    elif aws_integration is not None:
        current_mode = 'production'
    
    # Debug logging
    logger.info(f"Dashboard mode detection: latest_scan exists={latest_scan is not None}, "
                f"latest_scan mode={latest_scan.get('mode', 'N/A') if latest_scan else 'N/A'}, "
                f"aws_integration={aws_integration is not None}, "
                f"final current_mode={current_mode}, "
                f"demo_mode={current_mode == 'demo'}")
    
    # Generate statistics for the dashboard
    stats = {
        "total_resources": 0,
        "drift_detected": 0,
        "active_alerts": len(active_alerts),
        "last_scan": "Never",
        "next_scan": "Not scheduled",
        "scanner_status": "Running" if auto_scanner_running else "Stopped"
    }
    
    # Extract stats from latest scan if available
    if latest_scan:
        if 'drift_summary' in latest_scan:
            stats["total_resources"] = latest_scan["drift_summary"].get("total_resources_checked", 
                                       latest_scan.get("aws_resources", {}).get("total_resources", 0))
            stats["drift_detected"] = latest_scan["drift_summary"].get("total_drift_items", 0)
        
        stats["last_scan"] = latest_scan.get("timestamp", "Unknown")
        stats["next_scan"] = latest_scan.get("next_scan_scheduled", "Not scheduled")
    
    response = make_response(render_template('dashboard.html', 
                         demo_mode=(current_mode == 'demo'),
                         app_config=app_config,
                         latest_scan=latest_scan,
                         active_alerts=active_alerts[:5],  # Show only 5 most recent for dashboard
                         stats=stats))
    
    # Prevent caching to ensure mode changes are reflected immediately
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/status')
def api_status():
    """Get application status"""
    # Determine current mode from latest scan or AWS integration
    latest_scan = load_latest_scan()
    current_mode = 'demo'
    if latest_scan and 'mode' in latest_scan:
        current_mode = latest_scan['mode']
    elif aws_integration is not None:
        current_mode = 'production'
    
    return jsonify({
        'status': 'running',
        'mode': current_mode,
        'auto_scanner_running': auto_scanner_running,
        'scan_interval_minutes': app_config.scan_interval_minutes,
        'aws_connected': aws_integration is not None,
        'last_scan_id': current_scan_id,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/latest-scan')
def api_latest_scan():
    """Get latest scan results"""
    try:
        latest_file = f"{app_config.data_dir}/latest_scan.json"
        if os.path.exists(latest_file):
            with open(latest_file, 'r') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({'error': 'No scan results available'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/scan-history')
def api_scan_history():
    """Get scan history"""
    try:
        scans_dir = f"{app_config.data_dir}/scans"
        scan_files = []
        
        if os.path.exists(scans_dir):
            for filename in os.listdir(scans_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(scans_dir, filename)
                    with open(filepath, 'r') as f:
                        scan_data = json.load(f)
                        scan_files.append({
                            'filename': filename,
                            'scan_id': scan_data.get('scan_id'),
                            'timestamp': scan_data.get('timestamp'),
                            'mode': scan_data.get('mode'),
                            'total_drift_items': scan_data.get('drift_summary', {}).get('total_drift_items', 0)
                        })
        
        # Sort by timestamp (newest first)
        scan_files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to max_scan_history
        scan_files = scan_files[:app_config.max_scan_history]
        
        return jsonify(scan_files)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/alerts')
def api_alerts():
    """Get recent alerts"""
    try:
        alerts_dir = f"{app_config.data_dir}/alerts"
        all_alerts = []
        
        if os.path.exists(alerts_dir):
            for filename in os.listdir(alerts_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(alerts_dir, filename)
                    with open(filepath, 'r') as f:
                        alerts_data = json.load(f)
                        all_alerts.extend(alerts_data)
        
        # Sort by timestamp (newest first)
        all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to max_alert_history
        all_alerts = all_alerts[:app_config.max_alert_history]
        
        return jsonify(all_alerts)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/trigger-scan', methods=['POST'])
def api_trigger_scan():
    """Manually trigger a drift scan"""
    try:
        scan_results = scanner.perform_scan()
        response = jsonify({
            'success': True,
            'scan_id': scan_results['scan_id'],
            'timestamp': scan_results['timestamp']
        })
        # Prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        # Prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

@app.route('/api/toggle-auto-scan', methods=['POST'])
def api_toggle_auto_scan():
    """Toggle auto scanner on/off"""
    global auto_scanner_running
    
    try:
        if auto_scanner_running:
            auto_scanner_running = False
            return jsonify({'auto_scanner_running': False, 'message': 'Auto scanner stopped'})
        else:
            auto_scanner_running = True
            thread = threading.Thread(target=auto_scanner, daemon=True)
            thread.start()
            return jsonify({'auto_scanner_running': True, 'message': 'Auto scanner started'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/scan-results')
def scan_results():
    """Scan results page"""
    return render_template('scan_results.html', demo_mode=demo_mode)

@app.route('/alerts')
def alerts():
    """Alerts page"""
    return render_template('alerts.html', demo_mode=demo_mode)

@app.route('/api/aws-test')
def api_aws_test():
    """Test AWS connection"""
    if not aws_integration:
        return jsonify({
            'success': False,
            'error': 'AWS integration not configured'
        })
        
    try:
        result = aws_integration.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/config')
def config_page():
    """Configuration page"""
    return render_template('config.html', 
                         app_config=app_config, 
                         demo_mode=demo_mode)

if __name__ == '__main__':
    # Start auto scanner if enabled
    if app_config.enable_auto_scan:
        auto_scanner_running = True
        auto_scanner_thread = threading.Thread(target=auto_scanner, daemon=True)
        auto_scanner_thread.start()
        logger.info("Auto scanner started")
    
    # Run Flask app
    logger.info(f"Starting drift detection app on {app_config.host}:{app_config.port}")
    logger.info(f"Mode: {'Demo' if demo_mode else 'Production'}")
    logger.info(f"AWS Integration: {'Disabled' if aws_integration is None else 'Enabled'}")
    
    app.run(
        host=app_config.host,
        port=app_config.port,
        debug=app_config.debug
    )
