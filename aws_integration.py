"""
AWS Integration Module for Terraform Drift Detection
Handles real AWS resource scanning and S3 state file access with secure authentication
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from dataclasses import dataclass
import tempfile

logger = logging.getLogger(__name__)

@dataclass
class AWSConfig:
    """AWS configuration settings"""
    region: str = 'us-east-1'
    profile: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_state_key: Optional[str] = None
    assume_role_arn: Optional[str] = None
    
class AWSCredentialManager:
    """Manages AWS credentials securely"""
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self._session = None
        
    def get_session(self) -> boto3.Session:
        """Get authenticated AWS session with fallback authentication methods"""
        if self._session:
            return self._session
            
        # Priority order for authentication:
        # 1. Explicit credentials (for testing)
        # 2. IAM role (when running on Azure with cross-cloud auth)
        # 3. Environment variables
        # 4. AWS profile
        # 5. Default credential chain
        
        try:
            if self.config.access_key_id and self.config.secret_access_key:
                logger.info("Using explicit AWS credentials")
                self._session = boto3.Session(
                    aws_access_key_id=self.config.access_key_id,
                    aws_secret_access_key=self.config.secret_access_key,
                    aws_session_token=self.config.session_token,
                    region_name=self.config.region
                )
            elif self.config.assume_role_arn:
                logger.info(f"Using assume role: {self.config.assume_role_arn}")
                self._session = self._create_assume_role_session()
            elif self.config.profile:
                logger.info(f"Using AWS profile: {self.config.profile}")
                self._session = boto3.Session(
                    profile_name=self.config.profile,
                    region_name=self.config.region
                )
            else:
                logger.info("Using default AWS credential chain")
                self._session = boto3.Session(region_name=self.config.region)
                
            # Test credentials
            sts_client = self._session.client('sts')
            identity = sts_client.get_caller_identity()
            logger.info(f"Successfully authenticated as: {identity.get('Arn', 'Unknown')}")
            
            return self._session
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credential error: {e}")
            raise ValueError(f"AWS authentication failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected AWS authentication error: {e}")
            raise
            
    def _create_assume_role_session(self) -> boto3.Session:
        """Create session using assume role"""
        # Create initial session for STS
        temp_session = boto3.Session(region_name=self.config.region)
        sts_client = temp_session.client('sts')
        
        # Assume role
        response = sts_client.assume_role(
            RoleArn=self.config.assume_role_arn,
            RoleSessionName=f"drift-detection-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        credentials = response['Credentials']
        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=self.config.region
        )

class TerraformStateRetriever:
    """Retrieves and parses Terraform state files from S3"""
    
    def __init__(self, credential_manager: AWSCredentialManager):
        self.credential_manager = credential_manager
        
    def get_state_from_s3(self, bucket: str, key: str) -> Dict[str, Any]:
        """Download and parse Terraform state file from S3"""
        try:
            session = self.credential_manager.get_session()
            s3_client = session.client('s3')
            
            logger.info(f"Downloading Terraform state from s3://{bucket}/{key}")
            
            # Download state file
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
                s3_client.download_fileobj(bucket, key, temp_file)
                temp_file_path = temp_file.name
                
            # Read and parse JSON
            with open(temp_file_path, 'r') as f:
                state_data = json.load(f)
                
            # Cleanup temp file
            os.unlink(temp_file_path)
            
            logger.info(f"Successfully loaded Terraform state version {state_data.get('version', 'unknown')}")
            return state_data
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchBucket':
                raise ValueError(f"S3 bucket '{bucket}' does not exist")
            elif error_code == 'NoSuchKey':
                raise ValueError(f"Terraform state file '{key}' not found in bucket '{bucket}'")
            elif error_code == 'AccessDenied':
                raise ValueError(f"Access denied to s3://{bucket}/{key}. Check IAM permissions.")
            else:
                raise ValueError(f"S3 error ({error_code}): {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Terraform state file: {e}")
        except Exception as e:
            logger.error(f"Error retrieving Terraform state: {e}")
            raise

class AWSResourceScanner:
    """Scans live AWS resources across multiple services"""
    
    def __init__(self, credential_manager: AWSCredentialManager):
        self.credential_manager = credential_manager
        
    def scan_all_resources(self, regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scan all supported AWS resources across specified regions"""
        if regions is None:
            regions = [self.credential_manager.config.region]
            
        all_resources = {}
        
        for region in regions:
            logger.info(f"Scanning AWS resources in region: {region}")
            
            # Create region-specific session
            session = self.credential_manager.get_session()
            
            region_resources = {
                'region': region,
                'ec2_instances': self._scan_ec2_instances(session, region),
                'security_groups': self._scan_security_groups(session, region),
                's3_buckets': self._scan_s3_buckets(session, region),
                'rds_instances': self._scan_rds_instances(session, region),
                'lambda_functions': self._scan_lambda_functions(session, region),
                'iam_roles': self._scan_iam_roles(session, region),
                'vpcs': self._scan_vpcs(session, region),
                'subnets': self._scan_subnets(session, region),
                'load_balancers': self._scan_load_balancers(session, region)
            }
            
            all_resources[region] = region_resources
            
        return all_resources
        
    def _scan_ec2_instances(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan EC2 instances"""
        try:
            ec2_client = session.client('ec2', region_name=region)
            response = ec2_client.describe_instances()
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Skip terminated instances
                    if instance['State']['Name'] == 'terminated':
                        continue
                        
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'ImageId': instance['ImageId'],
                        'State': instance['State'],
                        'Placement': instance.get('Placement', {}),
                        'SecurityGroups': instance.get('SecurityGroups', []),
                        'Tags': instance.get('Tags', []),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'VpcId': instance.get('VpcId'),
                        'SubnetId': instance.get('SubnetId'),
                        'LaunchTime': instance['LaunchTime'].isoformat() if 'LaunchTime' in instance else None
                    })
                    
            logger.info(f"Found {len(instances)} EC2 instances in {region}")
            return instances
            
        except ClientError as e:
            logger.error(f"Error scanning EC2 instances in {region}: {e}")
            return []
            
    def _scan_security_groups(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan Security Groups"""
        try:
            ec2_client = session.client('ec2', region_name=region)
            response = ec2_client.describe_security_groups()
            
            security_groups = []
            for sg in response['SecurityGroups']:
                security_groups.append({
                    'GroupId': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'Description': sg['Description'],
                    'VpcId': sg.get('VpcId'),
                    'IpPermissions': sg.get('IpPermissions', []),
                    'IpPermissionsEgress': sg.get('IpPermissionsEgress', []),
                    'Tags': sg.get('Tags', [])
                })
                
            logger.info(f"Found {len(security_groups)} security groups in {region}")
            return security_groups
            
        except ClientError as e:
            logger.error(f"Error scanning security groups in {region}: {e}")
            return []
            
    def _scan_s3_buckets(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan S3 buckets (global but filtered by region)"""
        try:
            s3_client = session.client('s3', region_name=region)
            response = s3_client.list_buckets()
            
            buckets = []
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket location to filter by region
                    location_response = s3_client.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location_response.get('LocationConstraint')
                    
                    # Handle special cases for bucket location
                    if bucket_region is None:
                        bucket_region = 'us-east-1'  # Default region
                    elif bucket_region == 'EU':
                        bucket_region = 'eu-west-1'
                        
                    # Only include buckets in the specified region
                    if bucket_region != region:
                        continue
                        
                    # Get additional bucket details
                    bucket_info = {
                        'Name': bucket_name,
                        'CreationDate': bucket['CreationDate'].isoformat(),
                        'Region': bucket_region
                    }
                    
                    # Get versioning status
                    try:
                        versioning_response = s3_client.get_bucket_versioning(Bucket=bucket_name)
                        bucket_info['Versioning'] = versioning_response
                    except ClientError:
                        bucket_info['Versioning'] = {'Status': 'Disabled'}
                        
                    # Get encryption configuration
                    try:
                        encryption_response = s3_client.get_bucket_encryption(Bucket=bucket_name)
                        bucket_info['Encryption'] = encryption_response.get('ServerSideEncryptionConfiguration', {})
                    except ClientError:
                        bucket_info['Encryption'] = {}
                        
                    # Get tags
                    try:
                        tags_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                        bucket_info['Tags'] = tags_response.get('TagSet', [])
                    except ClientError:
                        bucket_info['Tags'] = []
                        
                    buckets.append(bucket_info)
                    
                except ClientError as e:
                    logger.warning(f"Error getting details for bucket {bucket_name}: {e}")
                    continue
                    
            logger.info(f"Found {len(buckets)} S3 buckets in {region}")
            return buckets
            
        except ClientError as e:
            logger.error(f"Error scanning S3 buckets: {e}")
            return []
            
    def _scan_rds_instances(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan RDS instances"""
        try:
            rds_client = session.client('rds', region_name=region)
            response = rds_client.describe_db_instances()
            
            instances = []
            for db in response['DBInstances']:
                instances.append({
                    'DBInstanceIdentifier': db['DBInstanceIdentifier'],
                    'DBInstanceClass': db['DBInstanceClass'],
                    'Engine': db['Engine'],
                    'EngineVersion': db['EngineVersion'],
                    'DBInstanceStatus': db['DBInstanceStatus'],
                    'MasterUsername': db.get('MasterUsername'),
                    'AllocatedStorage': db.get('AllocatedStorage'),
                    'StorageType': db.get('StorageType'),
                    'VpcId': db.get('DbSubnetGroup', {}).get('VpcId'),
                    'Tags': self._get_rds_tags(rds_client, db['DBInstanceArn'])
                })
                
            logger.info(f"Found {len(instances)} RDS instances in {region}")
            return instances
            
        except ClientError as e:
            logger.error(f"Error scanning RDS instances in {region}: {e}")
            return []
            
    def _scan_lambda_functions(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan Lambda functions"""
        try:
            lambda_client = session.client('lambda', region_name=region)
            response = lambda_client.list_functions()
            
            functions = []
            for func in response['Functions']:
                # Get tags for each function
                tags = {}
                try:
                    tags_response = lambda_client.list_tags(Resource=func['FunctionArn'])
                    tags = tags_response.get('Tags', {})
                except ClientError:
                    pass
                    
                functions.append({
                    'FunctionName': func['FunctionName'],
                    'FunctionArn': func['FunctionArn'],
                    'Runtime': func.get('Runtime'),
                    'Handler': func.get('Handler'),
                    'CodeSize': func.get('CodeSize'),
                    'Description': func.get('Description'),
                    'Timeout': func.get('Timeout'),
                    'MemorySize': func.get('MemorySize'),
                    'LastModified': func.get('LastModified'),
                    'Tags': [{'Key': k, 'Value': v} for k, v in tags.items()]
                })
                
            logger.info(f"Found {len(functions)} Lambda functions in {region}")
            return functions
            
        except ClientError as e:
            logger.error(f"Error scanning Lambda functions in {region}: {e}")
            return []
            
    def _scan_iam_roles(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan IAM roles (global service)"""
        # Only scan IAM roles once (not per region)
        if region != self.credential_manager.config.region:
            return []
            
        try:
            iam_client = session.client('iam')
            response = iam_client.list_roles()
            
            roles = []
            for role in response['Roles']:
                # Get tags for each role
                tags = []
                try:
                    tags_response = iam_client.list_role_tags(RoleName=role['RoleName'])
                    tags = tags_response.get('Tags', [])
                except ClientError:
                    pass
                    
                roles.append({
                    'RoleName': role['RoleName'],
                    'RoleId': role['RoleId'],
                    'Arn': role['Arn'],
                    'Path': role['Path'],
                    'CreateDate': role['CreateDate'].isoformat(),
                    'AssumeRolePolicyDocument': role.get('AssumeRolePolicyDocument'),
                    'Description': role.get('Description'),
                    'Tags': tags
                })
                
            logger.info(f"Found {len(roles)} IAM roles")
            return roles
            
        except ClientError as e:
            logger.error(f"Error scanning IAM roles: {e}")
            return []
            
    def _scan_vpcs(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan VPCs"""
        try:
            ec2_client = session.client('ec2', region_name=region)
            response = ec2_client.describe_vpcs()
            
            vpcs = []
            for vpc in response['Vpcs']:
                vpcs.append({
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock'],
                    'State': vpc['State'],
                    'IsDefault': vpc.get('IsDefault', False),
                    'Tags': vpc.get('Tags', [])
                })
                
            logger.info(f"Found {len(vpcs)} VPCs in {region}")
            return vpcs
            
        except ClientError as e:
            logger.error(f"Error scanning VPCs in {region}: {e}")
            return []
            
    def _scan_subnets(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan Subnets"""
        try:
            ec2_client = session.client('ec2', region_name=region)
            response = ec2_client.describe_subnets()
            
            subnets = []
            for subnet in response['Subnets']:
                subnets.append({
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'CidrBlock': subnet['CidrBlock'],
                    'AvailabilityZone': subnet['AvailabilityZone'],
                    'State': subnet['State'],
                    'MapPublicIpOnLaunch': subnet.get('MapPublicIpOnLaunch', False),
                    'Tags': subnet.get('Tags', [])
                })
                
            logger.info(f"Found {len(subnets)} subnets in {region}")
            return subnets
            
        except ClientError as e:
            logger.error(f"Error scanning subnets in {region}: {e}")
            return []
            
    def _scan_load_balancers(self, session: boto3.Session, region: str) -> List[Dict[str, Any]]:
        """Scan Load Balancers (ALB/NLB)"""
        try:
            elbv2_client = session.client('elbv2', region_name=region)
            response = elbv2_client.describe_load_balancers()
            
            load_balancers = []
            for lb in response['LoadBalancers']:
                # Get tags for each load balancer
                tags = []
                try:
                    tags_response = elbv2_client.describe_tags(ResourceArns=[lb['LoadBalancerArn']])
                    if tags_response['TagDescriptions']:
                        tags = tags_response['TagDescriptions'][0].get('Tags', [])
                except ClientError:
                    pass
                    
                load_balancers.append({
                    'LoadBalancerArn': lb['LoadBalancerArn'],
                    'LoadBalancerName': lb['LoadBalancerName'],
                    'DNSName': lb['DNSName'],
                    'Scheme': lb['Scheme'],
                    'Type': lb['Type'],
                    'State': lb['State'],
                    'VpcId': lb.get('VpcId'),
                    'AvailabilityZones': lb.get('AvailabilityZones', []),
                    'SecurityGroups': lb.get('SecurityGroups', []),
                    'Tags': tags
                })
                
            logger.info(f"Found {len(load_balancers)} load balancers in {region}")
            return load_balancers
            
        except ClientError as e:
            logger.error(f"Error scanning load balancers in {region}: {e}")
            return []
            
    def _get_rds_tags(self, rds_client, resource_arn: str) -> List[Dict[str, str]]:
        """Get tags for RDS resource"""
        try:
            response = rds_client.list_tags_for_resource(ResourceName=resource_arn)
            return response.get('TagList', [])
        except ClientError:
            return []

class AWSIntegration:
    """Main class orchestrating AWS integration"""
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self.credential_manager = AWSCredentialManager(config)
        self.state_retriever = TerraformStateRetriever(self.credential_manager)
        self.resource_scanner = AWSResourceScanner(self.credential_manager)
        
    def test_connection(self) -> Dict[str, Any]:
        """Test AWS connection and return account information"""
        try:
            session = self.credential_manager.get_session()
            sts_client = session.client('sts')
            
            identity = sts_client.get_caller_identity()
            
            return {
                'success': True,
                'account_id': identity.get('Account'),
                'user_arn': identity.get('Arn'),
                'user_id': identity.get('UserId'),
                'region': self.config.region
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_terraform_state(self) -> Optional[Dict[str, Any]]:
        """Get Terraform state from configured S3 location"""
        if not self.config.s3_bucket or not self.config.s3_state_key:
            raise ValueError("S3 bucket and state key must be configured")
            
        return self.state_retriever.get_state_from_s3(
            self.config.s3_bucket, 
            self.config.s3_state_key
        )
        
    def scan_aws_resources(self, regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scan live AWS resources"""
        return self.resource_scanner.scan_all_resources(regions)
        
    @classmethod
    def from_environment(cls) -> 'AWSIntegration':
        """Create AWS integration from environment variables"""
        config = AWSConfig(
            region=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            profile=os.getenv('AWS_PROFILE'),
            access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            session_token=os.getenv('AWS_SESSION_TOKEN'),
            s3_bucket=os.getenv('TERRAFORM_S3_BUCKET'),
            s3_state_key=os.getenv('TERRAFORM_S3_KEY'),
            assume_role_arn=os.getenv('AWS_ASSUME_ROLE_ARN')
        )
        
        return cls(config)
