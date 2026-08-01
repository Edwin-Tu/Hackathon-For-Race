#!/usr/bin/env python3
"""
Deploy RDS MySQL and Sync Prisma Schema
This script:
1. Creates an RDS MySQL instance
2. Waits for it to be available
3. Updates .env with the new connection string
4. Runs Prisma migrations to sync the schema
"""

import boto3
import os
import sys
import json
import subprocess
from datetime import datetime
from botocore.exceptions import ClientError

# Configuration
DB_INSTANCE_IDENTIFIER = "smart-care-agent-db"
DB_NAME = "smart_care_agent"
MASTER_USERNAME = "smart_care_app"
MASTER_PASSWORD = "Hackathon2026SecurePass!"
DB_INSTANCE_CLASS = "db.t3.micro"  # Free tier eligible
ALLOCATED_STORAGE = 20  # GB
ENGINE = "mysql"
ENGINE_VERSION = "8.0.46"
REGION = "us-west-2"

def load_credentials():
    """Load AWS credentials from .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

def create_or_get_rds_instance():
    """Create RDS instance or get existing one"""
    print("=" * 70)
    print("Step 1: Creating/Getting RDS MySQL Instance")
    print("=" * 70)
    
    load_credentials()
    rds = boto3.client('rds', region_name=REGION)
    
    try:
        # Check if instance already exists
        response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
        db_instance = response['DBInstances'][0]
        print(f"\n[INFO] Instance '{DB_INSTANCE_IDENTIFIER}' already exists")
        print(f"[INFO] Status: {db_instance['DBInstanceStatus']}")
        
        if db_instance['DBInstanceStatus'] != 'available':
            print(f"[INFO] Waiting for instance to become available...")
            waiter = rds.get_waiter('db_instance_available')
            waiter.wait(
                DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
                WaiterConfig={'Delay': 30, 'MaxAttempts': 40}
            )
            response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
            db_instance = response['DBInstances'][0]
        
        return db_instance
        
    except ClientError as e:
        if e.response['Error']['Code'] != 'DBInstanceNotFound':
            raise
    
    # Create new instance
    print(f"\n[INFO] Creating new RDS instance: {DB_INSTANCE_IDENTIFIER}")
    print(f"[INFO] Engine: {ENGINE} {ENGINE_VERSION}")
    print(f"[INFO] Instance Class: {DB_INSTANCE_CLASS}")
    print(f"[INFO] This will take 5-10 minutes...")
    
    try:
        response = rds.create_db_instance(
            DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
            DBName=DB_NAME,
            MasterUsername=MASTER_USERNAME,
            MasterUserPassword=MASTER_PASSWORD,
            DBInstanceClass=DB_INSTANCE_CLASS,
            Engine=ENGINE,
            EngineVersion=ENGINE_VERSION,
            AllocatedStorage=ALLOCATED_STORAGE,
            StorageType='gp3',
            StorageEncrypted=True,
            BackupRetentionPeriod=7,
            PubliclyAccessible=True,  # For development - change in production
            EnableCloudwatchLogsExports=['error', 'general', 'slowquery'],
            DeletionProtection=False,  # Set to True in production
            Tags=[
                {'Key': 'Project', 'Value': 'Hackathon-For-Race'},
                {'Key': 'Component', 'Value': 'SmartCareAgent'},
                {'Key': 'Environment', 'Value': 'Development'},
            ]
        )
        
        print(f"[OK] RDS instance creation initiated")
        print(f"[INFO] Waiting for instance to become available...")
        
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(
            DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 40}
        )
        
        response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
        return response['DBInstances'][0]
        
    except ClientError as e:
        print(f"[ERROR] Failed to create RDS instance: {e}")
        sys.exit(1)

def configure_security_group(db_instance):
    """Configure security group for MySQL access"""
    print("\n" + "=" * 70)
    print("Step 2: Configuring Security Group")
    print("=" * 70)
    
    ec2 = boto3.client('ec2', region_name=REGION)
    
    try:
        vpc_security_groups = db_instance.get('VpcSecurityGroups', [])
        if not vpc_security_groups:
            print("[WARNING] No security groups found")
            return
        
        security_group_id = vpc_security_groups[0]['VpcSecurityGroupId']
        print(f"[INFO] Security Group ID: {security_group_id}")
        
        try:
            ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 3306,
                        'ToPort': 3306,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'MySQL access'}]
                    }
                ]
            )
            print("[OK] Security group configured")
            print("[WARNING] Allows access from anywhere (0.0.0.0/0)")
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                print("[INFO] Security group already configured")
            else:
                print(f"[WARNING] Could not configure security group: {e}")
                
    except Exception as e:
        print(f"[WARNING] Security group configuration error: {e}")

def update_env_file(endpoint, port):
    """Update .env file with new DATABASE_URL"""
    print("\n" + "=" * 70)
    print("Step 3: Updating .env File")
    print("=" * 70)
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    new_database_url = f"mysql://{MASTER_USERNAME}:{MASTER_PASSWORD}@{endpoint}:{port}/{DB_NAME}"
    
    if not os.path.exists(env_path):
        print("[ERROR] .env file not found")
        return False
    
    # Read current .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update DATABASE_URL
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('DATABASE_URL='):
            # Keep old one as backup comment
            lines[i] = f'# OLD: {line}'
            lines.insert(i + 1, f'DATABASE_URL="{new_database_url}"\n')
            updated = True
            break
    
    if not updated:
        # Add new DATABASE_URL
        lines.insert(0, f'DATABASE_URL="{new_database_url}"\n')
    
    # Write updated .env
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"[OK] Updated DATABASE_URL in .env")
    print(f"[INFO] New connection string:")
    print(f"       {new_database_url}")
    return True

def run_prisma_migrations():
    """Run Prisma migrations to sync schema"""
    print("\n" + "=" * 70)
    print("Step 4: Running Prisma Migrations")
    print("=" * 70)
    
    project_root = os.path.join(os.path.dirname(__file__), '..')
    
    # Check if prisma is installed
    try:
        result = subprocess.run(
            ['npx', 'prisma', '--version'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        print(f"[INFO] Prisma version: {result.stdout.split()[0] if result.stdout else 'installed'}")
    except Exception as e:
        print(f"[ERROR] Prisma not found. Please run: npm install prisma")
        return False
    
    # Generate Prisma Client
    print("\n[INFO] Generating Prisma Client...")
    try:
        result = subprocess.run(
            ['npx', 'prisma', 'generate'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("[OK] Prisma Client generated")
        else:
            print(f"[WARNING] Prisma generate output: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] Failed to generate Prisma Client: {e}")
        return False
    
    # Deploy migrations
    print("\n[INFO] Deploying migrations to RDS MySQL...")
    try:
        result = subprocess.run(
            ['npx', 'prisma', 'migrate', 'deploy'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("[OK] Migrations deployed successfully!")
            return True
        else:
            print(f"[ERROR] Migration failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Migration timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run migrations: {e}")
        return False

def verify_connection():
    """Verify database connection"""
    print("\n" + "=" * 70)
    print("Step 5: Verifying Connection")
    print("=" * 70)
    
    project_root = os.path.join(os.path.dirname(__file__), '..')
    
    try:
        result = subprocess.run(
            ['npx', 'prisma', 'db', 'pull', '--force'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("[OK] Database connection verified!")
            return True
        else:
            print(f"[WARNING] Connection test: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[WARNING] Could not verify connection: {e}")
        return False

def save_connection_info(db_instance):
    """Save connection info to JSON file"""
    endpoint = db_instance['Endpoint']['Address']
    port = db_instance['Endpoint']['Port']
    
    connection_info = {
        'instance_id': DB_INSTANCE_IDENTIFIER,
        'endpoint': endpoint,
        'port': port,
        'database': DB_NAME,
        'username': MASTER_USERNAME,
        'password': MASTER_PASSWORD,
        'connection_string': f"mysql://{MASTER_USERNAME}:{MASTER_PASSWORD}@{endpoint}:{port}/{DB_NAME}",
        'region': REGION,
        'engine': ENGINE,
        'engine_version': ENGINE_VERSION,
        'status': db_instance['DBInstanceStatus'],
        'deployed_at': datetime.utcnow().isoformat()
    }
    
    output_file = os.path.join(os.path.dirname(__file__), '..', 'rds_connection_info.json')
    with open(output_file, 'w') as f:
        json.dump(connection_info, f, indent=2)
    
    print(f"\n[INFO] Connection details saved to: rds_connection_info.json")
    return connection_info

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy RDS MySQL and sync Prisma schema')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    parser.add_argument('--skip-migrations', action='store_true', help='Skip Prisma migrations')
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("Smart Care Agent - RDS MySQL Deployment + Prisma Sync")
    print("=" * 70)
    print(f"\nThis script will:")
    print(f"  1. Create RDS MySQL instance (or use existing)")
    print(f"  2. Configure security group")
    print(f"  3. Update .env with new DATABASE_URL")
    print(f"  4. Run Prisma migrations to sync schema")
    print(f"\nEstimated cost: ~$15-20/month (db.t3.micro)")
    print(f"Deployment time: 5-10 minutes for new instance")
    
    if not args.yes:
        print("\nPress Enter to continue or Ctrl+C to cancel...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n[INFO] Deployment cancelled")
            sys.exit(0)
    else:
        print("\n[INFO] Auto-confirming deployment (--yes flag)")
    
    # Step 1: Create/Get RDS instance
    db_instance = create_or_get_rds_instance()
    
    if not db_instance.get('Endpoint'):
        print("[ERROR] Database instance has no endpoint")
        sys.exit(1)
    
    endpoint = db_instance['Endpoint']['Address']
    port = db_instance['Endpoint']['Port']
    
    print(f"\n[OK] Database is available!")
    print(f"[INFO] Endpoint: {endpoint}")
    print(f"[INFO] Port: {port}")
    
    # Step 2: Configure security group
    configure_security_group(db_instance)
    
    # Step 3: Update .env
    if not update_env_file(endpoint, port):
        print("[ERROR] Failed to update .env file")
        sys.exit(1)
    
    # Step 4: Run Prisma migrations
    if not args.skip_migrations:
        if not run_prisma_migrations():
            print("\n[WARNING] Migrations failed, but database is created")
            print("[INFO] You can manually run: npx prisma migrate deploy")
    else:
        print("\n[INFO] Skipping Prisma migrations (--skip-migrations flag)")
    
    # Step 5: Verify connection
    verify_connection()
    
    # Save connection info
    connection_info = save_connection_info(db_instance)
    
    # Summary
    print("\n" + "=" * 70)
    print("[OK] Deployment Completed Successfully!")
    print("=" * 70)
    print(f"\nDatabase Details:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Port: {port}")
    print(f"  Database: {DB_NAME}")
    print(f"  Username: {MASTER_USERNAME}")
    print(f"  Password: {MASTER_PASSWORD}")
    print(f"\nConnection String (already in .env):")
    print(f"  {connection_info['connection_string']}")
    print(f"\nNext Steps:")
    print(f"  1. Test your application with the new database")
    print(f"  2. Import any existing data if needed")
    print(f"  3. Update your frontend to use the new backend API")
    print(f"\nTo delete the instance later:")
    print(f"  aws rds delete-db-instance --db-instance-identifier {DB_INSTANCE_IDENTIFIER} --skip-final-snapshot")
    print("=" * 70)
