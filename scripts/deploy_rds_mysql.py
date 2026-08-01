#!/usr/bin/env python3
"""
Deploy Amazon RDS MySQL Database for Smart Care Agent
This script creates an RDS MySQL instance with optimal settings for the Hackathon project.
"""

import boto3
import os
import sys
import time
import json
from botocore.exceptions import ClientError

# Configuration
DB_INSTANCE_IDENTIFIER = "smart-care-agent-db"
DB_NAME = "smart_care_agent"
MASTER_USERNAME = "smart_care_app"
MASTER_PASSWORD = "Hackathon2026SecurePass!"  # CHANGE THIS IN PRODUCTION
DB_INSTANCE_CLASS = "db.t3.micro"  # Free tier eligible / low cost
ALLOCATED_STORAGE = 20  # GB
ENGINE = "mysql"
ENGINE_VERSION = "8.0.35"
REGION = "us-west-2"

# Load AWS credentials from .env
def load_credentials():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

def create_rds_instance():
    """Create RDS MySQL instance"""
    print("=" * 70)
    print("Deploying Amazon RDS MySQL Database")
    print("=" * 70)
    
    load_credentials()
    
    rds = boto3.client('rds', region_name=REGION)
    
    print(f"\n[INFO] Creating RDS instance: {DB_INSTANCE_IDENTIFIER}")
    print(f"[INFO] Engine: {ENGINE} {ENGINE_VERSION}")
    print(f"[INFO] Instance Class: {DB_INSTANCE_CLASS}")
    print(f"[INFO] Storage: {ALLOCATED_STORAGE} GB")
    print(f"[INFO] Region: {REGION}")
    
    try:
        # Check if instance already exists
        try:
            response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
            print(f"\n[WARNING] Instance '{DB_INSTANCE_IDENTIFIER}' already exists!")
            db_instance = response['DBInstances'][0]
            print(f"[INFO] Status: {db_instance['DBInstanceStatus']}")
            
            if db_instance.get('Endpoint'):
                print(f"[INFO] Endpoint: {db_instance['Endpoint']['Address']}")
                print(f"[INFO] Port: {db_instance['Endpoint']['Port']}")
            
            return db_instance
        except ClientError as e:
            if e.response['Error']['Code'] != 'DBInstanceNotFound':
                raise
        
        # Create the RDS instance
        response = rds.create_db_instance(
            DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
            DBName=DB_NAME,
            MasterUsername=MASTER_USERNAME,
            MasterUserPassword=MASTER_PASSWORD,
            DBInstanceClass=DB_INSTANCE_CLASS,
            Engine=ENGINE,
            EngineVersion=ENGINE_VERSION,
            AllocatedStorage=ALLOCATED_STORAGE,
            StorageType='gp3',  # General Purpose SSD
            StorageEncrypted=True,
            BackupRetentionPeriod=7,  # 7 days backup retention
            PubliclyAccessible=True,  # Set to False in production!
            VpcSecurityGroupIds=[],  # Will use default VPC security group
            EnableCloudwatchLogsExports=['error', 'general', 'slowquery'],
            DeletionProtection=False,  # Set to True in production!
            Tags=[
                {'Key': 'Project', 'Value': 'Hackathon-For-Race'},
                {'Key': 'Component', 'Value': 'SmartCareAgent'},
                {'Key': 'Environment', 'Value': 'Development'},
            ]
        )
        
        print(f"\n[OK] RDS instance creation initiated!")
        print(f"[INFO] Instance ID: {response['DBInstance']['DBInstanceIdentifier']}")
        print(f"[INFO] Status: {response['DBInstance']['DBInstanceStatus']}")
        print(f"\n[INFO] Waiting for instance to become available (this may take 5-10 minutes)...")
        
        # Wait for the instance to be available
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(
            DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
            WaiterConfig={
                'Delay': 30,  # Check every 30 seconds
                'MaxAttempts': 40  # Maximum 20 minutes
            }
        )
        
        # Get the endpoint
        response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
        db_instance = response['DBInstances'][0]
        endpoint = db_instance['Endpoint']['Address']
        port = db_instance['Endpoint']['Port']
        
        print(f"\n[OK] RDS instance is now available!")
        print("=" * 70)
        print("Connection Details:")
        print("=" * 70)
        print(f"Endpoint: {endpoint}")
        print(f"Port: {port}")
        print(f"Database: {DB_NAME}")
        print(f"Username: {MASTER_USERNAME}")
        print(f"Password: {MASTER_PASSWORD}")
        print(f"\nConnection String:")
        print(f'DATABASE_URL="mysql://{MASTER_USERNAME}:{MASTER_PASSWORD}@{endpoint}:{port}/{DB_NAME}"')
        print("=" * 70)
        
        # Save connection details to file
        connection_info = {
            'endpoint': endpoint,
            'port': port,
            'database': DB_NAME,
            'username': MASTER_USERNAME,
            'password': MASTER_PASSWORD,
            'connection_string': f"mysql://{MASTER_USERNAME}:{MASTER_PASSWORD}@{endpoint}:{port}/{DB_NAME}"
        }
        
        output_file = os.path.join(os.path.dirname(__file__), '..', 'rds_connection_info.json')
        with open(output_file, 'w') as f:
            json.dump(connection_info, f, indent=2)
        
        print(f"\n[INFO] Connection details saved to: rds_connection_info.json")
        
        return db_instance
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DBInstanceAlreadyExists':
            print(f"\n[ERROR] Instance '{DB_INSTANCE_IDENTIFIER}' already exists!")
        elif error_code == 'InvalidParameterValue':
            print(f"\n[ERROR] Invalid parameter: {e}")
        elif error_code == 'AccessDenied':
            print(f"\n[ERROR] Access denied. Check your IAM permissions.")
        else:
            print(f"\n[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

def configure_security_group():
    """Configure security group to allow MySQL access"""
    print("\n" + "=" * 70)
    print("Configuring Security Group")
    print("=" * 70)
    
    ec2 = boto3.client('ec2', region_name=REGION)
    rds = boto3.client('rds', region_name=REGION)
    
    try:
        # Get the RDS instance
        response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
        db_instance = response['DBInstances'][0]
        
        # Get the VPC security group
        vpc_security_groups = db_instance.get('VpcSecurityGroups', [])
        if not vpc_security_groups:
            print("[WARNING] No VPC security groups found")
            return
        
        security_group_id = vpc_security_groups[0]['VpcSecurityGroupId']
        print(f"[INFO] Security Group ID: {security_group_id}")
        
        # Add inbound rule for MySQL (port 3306)
        try:
            ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 3306,
                        'ToPort': 3306,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'MySQL access from anywhere'}]
                    }
                ]
            )
            print("[OK] Security group configured to allow MySQL access (port 3306)")
            print("[WARNING] Current configuration allows access from anywhere (0.0.0.0/0)")
            print("[WARNING] In production, restrict this to specific IP addresses!")
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                print("[INFO] Security group rule already exists")
            else:
                print(f"[WARNING] Could not configure security group: {e}")
        
    except ClientError as e:
        print(f"[WARNING] Error configuring security group: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Smart Care Agent - RDS MySQL Deployment Script")
    print("=" * 70)
    print("\nThis script will create an Amazon RDS MySQL instance.")
    print(f"Estimated cost: ~$15-20/month (db.t3.micro)")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n[INFO] Deployment cancelled by user")
        sys.exit(0)
    
    # Create RDS instance
    create_rds_instance()
    
    # Configure security group
    configure_security_group()
    
    print("\n" + "=" * 70)
    print("[OK] Deployment completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update .env file with the new DATABASE_URL")
    print("2. Run database migrations")
    print("3. Test the connection")
    print("\nTo delete the instance later, run:")
    print(f"  aws rds delete-db-instance --db-instance-identifier {DB_INSTANCE_IDENTIFIER} --skip-final-snapshot")
    print("=" * 70)
