"""
Enhanced Drift Detection Engine
Compares Terraform state with live AWS resources to detect configuration drift
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class DriftItem:
    """Represents a detected drift between Terraform and AWS"""
    resource_type: str
    resource_name: str
    terraform_address: str
    aws_id: str
    drift_type: str  # 'configuration', 'missing', 'extra', 'tags'
    severity: str    # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    differences: Dict[str, Any]
    first_detected: str
    last_seen: str
    environment: str = 'production'
    region: str = 'us-east-1'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
        
    def get_hash(self) -> str:
        """Get unique hash for this drift item"""
        key_data = f"{self.terraform_address}:{self.aws_id}:{self.drift_type}"
        return hashlib.md5(key_data.encode()).hexdigest()

class DriftDetectionEngine:
    """Main drift detection engine"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.severity_thresholds = config.get('severity_thresholds', {
            "CRITICAL": ["missing", "extra"],
            "HIGH": ["configuration"],
            "MEDIUM": ["tags"],
            "LOW": ["metadata"]
        })
        self.ignore_tags = set(config.get('ignore_tags', ['LastModified', 'CreatedBy']))
        self.ignore_resources = set(config.get('ignore_resources', []))
        
    def detect_drift(self, terraform_state: Dict[str, Any], aws_resources: Dict[str, Any]) -> List[DriftItem]:
        """
        Main drift detection logic
        Compares Terraform state with live AWS resources
        """
        drift_items = []
        
        # Parse Terraform state to extract managed resources
        tf_resources = self._parse_terraform_state(terraform_state)
        
        # For each region in AWS resources
        for region, region_resources in aws_resources.items():
            if region == 'region':  # Skip metadata
                continue
                
            logger.info(f"Analyzing drift in region: {region}")
            
            # Detect drift for each resource type
            drift_items.extend(self._detect_ec2_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_security_group_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_s3_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_rds_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_lambda_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_iam_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_vpc_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_subnet_drift(tf_resources, region_resources, region))
            drift_items.extend(self._detect_load_balancer_drift(tf_resources, region_resources, region))
            
        # Detect extra AWS resources not in Terraform
        drift_items.extend(self._detect_extra_aws_resources(tf_resources, aws_resources))
        
        logger.info(f"Detected {len(drift_items)} drift items")
        return drift_items
        
    def _parse_terraform_state(self, terraform_state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Parse Terraform state file to extract managed resources by type"""
        tf_resources = {}
        
        resources = terraform_state.get('resources', [])
        for resource in resources:
            if resource.get('mode') != 'managed':
                continue
                
            resource_type = resource.get('type')
            if not resource_type:
                continue
                
            if resource_type not in tf_resources:
                tf_resources[resource_type] = []
                
            for instance in resource.get('instances', []):
                attributes = instance.get('attributes', {})
                tf_resource = {
                    'type': resource_type,
                    'name': resource.get('name'),
                    'address': f"{resource_type}.{resource.get('name')}",
                    'attributes': attributes
                }
                tf_resources[resource_type].append(tf_resource)
                
        return tf_resources
        
    def _detect_ec2_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in EC2 instances"""
        drift_items = []
        tf_instances = tf_resources.get('aws_instance', [])
        aws_instances = aws_resources.get('ec2_instances', [])
        
        for tf_instance in tf_instances:
            tf_attrs = tf_instance['attributes']
            tf_id = tf_attrs.get('id')
            
            # Find corresponding AWS instance
            aws_instance = None
            for aws_inst in aws_instances:
                if aws_inst['InstanceId'] == tf_id:
                    aws_instance = aws_inst
                    break
                    
            if not aws_instance:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type='aws_instance',
                    resource_name=tf_instance['name'],
                    terraform_address=tf_instance['address'],
                    aws_id=tf_id,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': 'Resource exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for configuration drift
            differences = {}
            
            # Instance type
            tf_type = tf_attrs.get('instance_type')
            aws_type = aws_instance.get('InstanceType')
            if tf_type != aws_type:
                differences['instance_type'] = {
                    'terraform': tf_type,
                    'aws': aws_type,
                    'impact': 'Performance and cost implications'
                }
                
            # AMI
            tf_ami = tf_attrs.get('ami')
            aws_ami = aws_instance.get('ImageId')
            if tf_ami != aws_ami:
                differences['ami'] = {
                    'terraform': tf_ami,
                    'aws': aws_ami,
                    'impact': 'Security and compatibility implications'
                }
                
            # Availability Zone
            tf_az = tf_attrs.get('availability_zone')
            aws_az = aws_instance.get('Placement', {}).get('AvailabilityZone')
            if tf_az != aws_az:
                differences['availability_zone'] = {
                    'terraform': tf_az,
                    'aws': aws_az,
                    'impact': 'Location and networking implications'
                }
                
            # Tags
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_instance.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Security Groups
            tf_sgs = set(tf_attrs.get('security_groups', []))
            aws_sgs = set([sg['GroupId'] for sg in aws_instance.get('SecurityGroups', [])])
            if tf_sgs != aws_sgs:
                differences['security_groups'] = {
                    'terraform': list(tf_sgs),
                    'aws': list(aws_sgs),
                    'impact': 'Network security implications'
                }
                
            # Create drift item if differences found
            if differences:
                drift_type = 'tags' if 'tags' in differences and len(differences) == 1 else 'configuration'
                drift_items.append(DriftItem(
                    resource_type='aws_instance',
                    resource_name=tf_instance['name'],
                    terraform_address=tf_instance['address'],
                    aws_id=tf_id,
                    drift_type=drift_type,
                    severity=self._get_severity(drift_type),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_security_group_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in Security Groups"""
        drift_items = []
        tf_sgs = tf_resources.get('aws_security_group', [])
        aws_sgs = aws_resources.get('security_groups', [])
        
        for tf_sg in tf_sgs:
            tf_attrs = tf_sg['attributes']
            tf_id = tf_attrs.get('id')
            
            # Find corresponding AWS security group
            aws_sg = None
            for aws_group in aws_sgs:
                if aws_group['GroupId'] == tf_id:
                    aws_sg = aws_group
                    break
                    
            if not aws_sg:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type='aws_security_group',
                    resource_name=tf_sg['name'],
                    terraform_address=tf_sg['address'],
                    aws_id=tf_id,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': 'Security group exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for configuration drift
            differences = {}
            
            # Name
            tf_name = tf_attrs.get('name')
            aws_name = aws_sg.get('GroupName')
            if tf_name != aws_name:
                differences['name'] = {
                    'terraform': tf_name,
                    'aws': aws_name
                }
                
            # Description
            tf_desc = tf_attrs.get('description')
            aws_desc = aws_sg.get('Description')
            if tf_desc != aws_desc:
                differences['description'] = {
                    'terraform': tf_desc,
                    'aws': aws_desc
                }
                
            # Ingress rules
            tf_ingress = tf_attrs.get('ingress', [])
            aws_ingress = aws_sg.get('IpPermissions', [])
            ingress_diff = self._compare_security_group_rules(tf_ingress, aws_ingress, 'ingress')
            if ingress_diff:
                differences['ingress_rules'] = ingress_diff
                
            # Tags
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_sg.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Create drift item if differences found
            if differences:
                drift_type = 'tags' if 'tags' in differences and len(differences) == 1 else 'configuration'
                drift_items.append(DriftItem(
                    resource_type='aws_security_group',
                    resource_name=tf_sg['name'],
                    terraform_address=tf_sg['address'],
                    aws_id=tf_id,
                    drift_type=drift_type,
                    severity=self._get_severity(drift_type),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_s3_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in S3 buckets"""
        drift_items = []
        tf_buckets = tf_resources.get('aws_s3_bucket', [])
        aws_buckets = aws_resources.get('s3_buckets', [])
        
        for tf_bucket in tf_buckets:
            tf_attrs = tf_bucket['attributes']
            tf_id = tf_attrs.get('id') or tf_attrs.get('bucket')
            
            # Find corresponding AWS bucket
            aws_bucket = None
            for aws_bkt in aws_buckets:
                if aws_bkt['Name'] == tf_id:
                    aws_bucket = aws_bkt
                    break
                    
            if not aws_bucket:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type='aws_s3_bucket',
                    resource_name=tf_bucket['name'],
                    terraform_address=tf_bucket['address'],
                    aws_id=tf_id,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': 'S3 bucket exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for configuration drift
            differences = {}
            
            # Versioning
            tf_versioning = tf_attrs.get('versioning', [{}])[0].get('enabled', False)
            aws_versioning = aws_bucket.get('Versioning', {}).get('Status') == 'Enabled'
            if tf_versioning != aws_versioning:
                differences['versioning'] = {
                    'terraform': tf_versioning,
                    'aws': aws_versioning,
                    'impact': 'Data protection and compliance implications'
                }
                
            # Encryption
            tf_encryption = self._extract_s3_encryption(tf_attrs)
            aws_encryption = self._extract_aws_s3_encryption(aws_bucket)
            if tf_encryption != aws_encryption:
                differences['encryption'] = {
                    'terraform': tf_encryption,
                    'aws': aws_encryption,
                    'impact': 'Security and compliance implications'
                }
                
            # Tags
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_bucket.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Create drift item if differences found
            if differences:
                drift_type = 'tags' if 'tags' in differences and len(differences) == 1 else 'configuration'
                drift_items.append(DriftItem(
                    resource_type='aws_s3_bucket',
                    resource_name=tf_bucket['name'],
                    terraform_address=tf_bucket['address'],
                    aws_id=tf_id,
                    drift_type=drift_type,
                    severity=self._get_severity(drift_type),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_rds_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in RDS instances"""
        drift_items = []
        tf_instances = tf_resources.get('aws_db_instance', [])
        aws_instances = aws_resources.get('rds_instances', [])
        
        for tf_instance in tf_instances:
            tf_attrs = tf_instance['attributes']
            tf_id = tf_attrs.get('id') or tf_attrs.get('identifier')
            
            # Find corresponding AWS RDS instance
            aws_instance = None
            for aws_inst in aws_instances:
                if aws_inst['DBInstanceIdentifier'] == tf_id:
                    aws_instance = aws_inst
                    break
                    
            if not aws_instance:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type='aws_db_instance',
                    resource_name=tf_instance['name'],
                    terraform_address=tf_instance['address'],
                    aws_id=tf_id,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': 'RDS instance exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for configuration drift
            differences = {}
            
            # Instance class
            tf_class = tf_attrs.get('instance_class')
            aws_class = aws_instance.get('DBInstanceClass')
            if tf_class != aws_class:
                differences['instance_class'] = {
                    'terraform': tf_class,
                    'aws': aws_class,
                    'impact': 'Performance and cost implications'
                }
                
            # Engine version
            tf_version = tf_attrs.get('engine_version')
            aws_version = aws_instance.get('EngineVersion')
            if tf_version and aws_version and tf_version != aws_version:
                differences['engine_version'] = {
                    'terraform': tf_version,
                    'aws': aws_version,
                    'impact': 'Compatibility and security implications'
                }
                
            # Storage
            tf_storage = tf_attrs.get('allocated_storage')
            aws_storage = aws_instance.get('AllocatedStorage')
            if tf_storage and aws_storage and int(tf_storage) != int(aws_storage):
                differences['allocated_storage'] = {
                    'terraform': tf_storage,
                    'aws': aws_storage,
                    'impact': 'Storage capacity and cost implications'
                }
                
            # Tags
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_instance.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Create drift item if differences found
            if differences:
                drift_type = 'tags' if 'tags' in differences and len(differences) == 1 else 'configuration'
                drift_items.append(DriftItem(
                    resource_type='aws_db_instance',
                    resource_name=tf_instance['name'],
                    terraform_address=tf_instance['address'],
                    aws_id=tf_id,
                    drift_type=drift_type,
                    severity=self._get_severity(drift_type),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_lambda_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in Lambda functions"""
        drift_items = []
        tf_functions = tf_resources.get('aws_lambda_function', [])
        aws_functions = aws_resources.get('lambda_functions', [])
        
        for tf_function in tf_functions:
            tf_attrs = tf_function['attributes']
            tf_name = tf_attrs.get('function_name')
            
            # Find corresponding AWS Lambda function
            aws_function = None
            for aws_func in aws_functions:
                if aws_func['FunctionName'] == tf_name:
                    aws_function = aws_func
                    break
                    
            if not aws_function:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type='aws_lambda_function',
                    resource_name=tf_function['name'],
                    terraform_address=tf_function['address'],
                    aws_id=tf_name,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': 'Lambda function exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for configuration drift
            differences = {}
            
            # Runtime
            tf_runtime = tf_attrs.get('runtime')
            aws_runtime = aws_function.get('Runtime')
            if tf_runtime != aws_runtime:
                differences['runtime'] = {
                    'terraform': tf_runtime,
                    'aws': aws_runtime,
                    'impact': 'Compatibility and performance implications'
                }
                
            # Memory size
            tf_memory = tf_attrs.get('memory_size')
            aws_memory = aws_function.get('MemorySize')
            if tf_memory and aws_memory and int(tf_memory) != int(aws_memory):
                differences['memory_size'] = {
                    'terraform': tf_memory,
                    'aws': aws_memory,
                    'impact': 'Performance and cost implications'
                }
                
            # Timeout
            tf_timeout = tf_attrs.get('timeout')
            aws_timeout = aws_function.get('Timeout')
            if tf_timeout and aws_timeout and int(tf_timeout) != int(aws_timeout):
                differences['timeout'] = {
                    'terraform': tf_timeout,
                    'aws': aws_timeout,
                    'impact': 'Function execution behavior'
                }
                
            # Tags
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_function.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Create drift item if differences found
            if differences:
                drift_type = 'tags' if 'tags' in differences and len(differences) == 1 else 'configuration'
                drift_items.append(DriftItem(
                    resource_type='aws_lambda_function',
                    resource_name=tf_function['name'],
                    terraform_address=tf_function['address'],
                    aws_id=tf_name,
                    drift_type=drift_type,
                    severity=self._get_severity(drift_type),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_iam_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in IAM roles"""
        drift_items = []
        tf_roles = tf_resources.get('aws_iam_role', [])
        
        # IAM is global, only check in primary region
        if region != self.config.get('aws_region', 'us-east-1'):
            return drift_items
            
        aws_roles = aws_resources.get('iam_roles', [])
        
        for tf_role in tf_roles:
            tf_attrs = tf_role['attributes']
            tf_name = tf_attrs.get('name')
            
            # Find corresponding AWS IAM role
            aws_role = None
            for aws_r in aws_roles:
                if aws_r['RoleName'] == tf_name:
                    aws_role = aws_r
                    break
                    
            if not aws_role:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type='aws_iam_role',
                    resource_name=tf_role['name'],
                    terraform_address=tf_role['address'],
                    aws_id=tf_name,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': 'IAM role exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for configuration drift
            differences = {}
            
            # Description
            tf_desc = tf_attrs.get('description')
            aws_desc = aws_role.get('Description')
            if tf_desc != aws_desc:
                differences['description'] = {
                    'terraform': tf_desc,
                    'aws': aws_desc
                }
                
            # Tags
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_role.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Create drift item if differences found
            if differences:
                drift_type = 'tags' if 'tags' in differences and len(differences) == 1 else 'configuration'
                drift_items.append(DriftItem(
                    resource_type='aws_iam_role',
                    resource_name=tf_role['name'],
                    terraform_address=tf_role['address'],
                    aws_id=tf_name,
                    drift_type=drift_type,
                    severity=self._get_severity(drift_type),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_vpc_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in VPCs"""
        return self._generic_detect_drift('aws_vpc', 'vpcs', tf_resources, aws_resources, region, 'VpcId')
        
    def _detect_subnet_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in Subnets"""
        return self._generic_detect_drift('aws_subnet', 'subnets', tf_resources, aws_resources, region, 'SubnetId')
        
    def _detect_load_balancer_drift(self, tf_resources: Dict, aws_resources: Dict, region: str) -> List[DriftItem]:
        """Detect drift in Load Balancers"""
        return self._generic_detect_drift('aws_lb', 'load_balancers', tf_resources, aws_resources, region, 'LoadBalancerName')
        
    def _generic_detect_drift(self, tf_type: str, aws_type: str, tf_resources: Dict, aws_resources: Dict, region: str, id_field: str) -> List[DriftItem]:
        """Generic drift detection for simpler resource types"""
        drift_items = []
        tf_items = tf_resources.get(tf_type, [])
        aws_items = aws_resources.get(aws_type, [])
        
        for tf_item in tf_items:
            tf_attrs = tf_item['attributes']
            tf_id = tf_attrs.get('id')
            
            # Find corresponding AWS resource
            aws_item = None
            for aws_i in aws_items:
                if aws_i.get(id_field) == tf_id:
                    aws_item = aws_i
                    break
                    
            if not aws_item:
                # Missing resource
                drift_items.append(DriftItem(
                    resource_type=tf_type,
                    resource_name=tf_item['name'],
                    terraform_address=tf_item['address'],
                    aws_id=tf_id,
                    drift_type='missing',
                    severity=self._get_severity('missing'),
                    differences={'status': f'{tf_type} exists in Terraform but not found in AWS'},
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                continue
                
            # Check for tag drift (common to most resources)
            differences = {}
            tag_diff = self._compare_tags(tf_attrs.get('tags', {}), aws_item.get('Tags', []))
            if tag_diff:
                differences['tags'] = tag_diff
                
            # Create drift item if differences found
            if differences:
                drift_items.append(DriftItem(
                    resource_type=tf_type,
                    resource_name=tf_item['name'],
                    terraform_address=tf_item['address'],
                    aws_id=tf_id,
                    drift_type='tags',
                    severity=self._get_severity('tags'),
                    differences=differences,
                    first_detected=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    region=region
                ))
                
        return drift_items
        
    def _detect_extra_aws_resources(self, tf_resources: Dict, aws_resources: Dict) -> List[DriftItem]:
        """Detect AWS resources that exist but are not in Terraform"""
        drift_items = []
        
        # Get all Terraform resource IDs by type
        tf_ids_by_type = {}
        for resource_type, resources in tf_resources.items():
            tf_ids_by_type[resource_type] = set()
            for resource in resources:
                resource_id = resource['attributes'].get('id')
                if resource_id:
                    tf_ids_by_type[resource_type].add(resource_id)
                    
        # Check each region
        for region, region_resources in aws_resources.items():
            if region == 'region':
                continue
                
            # Check EC2 instances
            for aws_instance in region_resources.get('ec2_instances', []):
                instance_id = aws_instance['InstanceId']
                if instance_id not in tf_ids_by_type.get('aws_instance', set()):
                    # Check if this is a managed resource (has ManagedBy tag)
                    tags = {tag['Key']: tag['Value'] for tag in aws_instance.get('Tags', [])}
                    if tags.get('ManagedBy') != 'terraform':
                        drift_items.append(DriftItem(
                            resource_type='aws_instance',
                            resource_name=tags.get('Name', instance_id),
                            terraform_address='N/A',
                            aws_id=instance_id,
                            drift_type='extra',
                            severity=self._get_severity('extra'),
                            differences={
                                'status': 'AWS resource exists but not managed by Terraform',
                                'resource_details': {
                                    'instance_type': aws_instance.get('InstanceType'),
                                    'state': aws_instance.get('State', {}).get('Name'),
                                    'tags': tags
                                }
                            },
                            first_detected=datetime.now().isoformat(),
                            last_seen=datetime.now().isoformat(),
                            region=region
                        ))
                        
            # Similar checks for other resource types can be added here
            
        return drift_items
        
    def _compare_tags(self, tf_tags: Dict[str, str], aws_tags: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Compare Terraform tags with AWS tags"""
        # Convert AWS tags to dict
        aws_tags_dict = {tag['Key']: tag['Value'] for tag in aws_tags}
        
        # Filter out ignored tags
        tf_filtered = {k: v for k, v in tf_tags.items() if k not in self.ignore_tags}
        aws_filtered = {k: v for k, v in aws_tags_dict.items() if k not in self.ignore_tags}
        
        if tf_filtered == aws_filtered:
            return None
            
        return {
            'terraform': tf_filtered,
            'aws': aws_filtered,
            'missing_in_aws': {k: v for k, v in tf_filtered.items() if k not in aws_filtered},
            'extra_in_aws': {k: v for k, v in aws_filtered.items() if k not in tf_filtered},
            'different_values': {
                k: {'terraform': tf_filtered[k], 'aws': aws_filtered[k]} 
                for k in tf_filtered.keys() & aws_filtered.keys() 
                if tf_filtered[k] != aws_filtered[k]
            }
        }
        
    def _compare_security_group_rules(self, tf_rules: List, aws_rules: List, rule_type: str) -> Optional[Dict[str, Any]]:
        """Compare security group rules"""
        # Normalize rules for comparison
        tf_normalized = self._normalize_sg_rules(tf_rules)
        aws_normalized = self._normalize_sg_rules(aws_rules, is_aws=True)
        
        if tf_normalized == aws_normalized:
            return None
            
        return {
            'terraform': tf_normalized,
            'aws': aws_normalized,
            'impact': f'Network security rules differ for {rule_type}'
        }
        
    def _normalize_sg_rules(self, rules: List, is_aws: bool = False) -> List[Dict]:
        """Normalize security group rules for comparison"""
        normalized = []
        
        for rule in rules:
            if is_aws:
                # AWS format
                normalized_rule = {
                    'protocol': rule.get('IpProtocol'),
                    'from_port': rule.get('FromPort'),
                    'to_port': rule.get('ToPort'),
                    'cidr_blocks': [ip_range['CidrIp'] for ip_range in rule.get('IpRanges', [])]
                }
            else:
                # Terraform format
                normalized_rule = {
                    'protocol': rule.get('protocol'),
                    'from_port': rule.get('from_port'),
                    'to_port': rule.get('to_port'),
                    'cidr_blocks': rule.get('cidr_blocks', [])
                }
                
            normalized.append(normalized_rule)
            
        # Sort for consistent comparison
        return sorted(normalized, key=lambda x: (x['protocol'], x['from_port'], x['to_port']))
        
    def _extract_s3_encryption(self, tf_attrs: Dict) -> str:
        """Extract S3 encryption algorithm from Terraform attributes"""
        encryption_config = tf_attrs.get('server_side_encryption_configuration', [{}])
        if encryption_config:
            rule = encryption_config[0].get('rule', [{}])
            if rule:
                default_encryption = rule[0].get('apply_server_side_encryption_by_default', [{}])
                if default_encryption:
                    return default_encryption[0].get('sse_algorithm', 'None')
        return 'None'
        
    def _extract_aws_s3_encryption(self, aws_bucket: Dict) -> str:
        """Extract S3 encryption algorithm from AWS bucket info"""
        encryption = aws_bucket.get('Encryption', {})
        rules = encryption.get('Rules', [])
        if rules:
            default_encryption = rules[0].get('ApplyServerSideEncryptionByDefault', {})
            return default_encryption.get('SSEAlgorithm', 'None')
        return 'None'
        
    def _get_severity(self, drift_type: str) -> str:
        """Get severity level based on drift type"""
        for severity, types in self.severity_thresholds.items():
            if drift_type in types:
                return severity
        return 'LOW'
