#!/usr/bin/env python3
"""
Deploy Amazon DynamoDB Tables for Smart Care Agent
This script creates DynamoDB tables as a serverless alternative to RDS MySQL.
DynamoDB is cheaper and scales automatically.
"""

import boto3
import os
import sys
import json
from botocore.exceptions import ClientError

REGION = "us-west-2"

# Table definitions
TABLES = [
    {
        'TableName': 'smart_care_residents',
        'KeySchema': [
            {'AttributeName': 'resident_id', 'KeyType': 'HASH'}  # Partition key
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'resident_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',  # On-demand pricing, no minimum cost
        'Tags': [
            {'Key': 'Project', 'Value': 'Hackathon-For-Race'},
            {'Key': 'Component', 'Value': 'SmartCareAgent'},
        ]
    },
    {
        'TableName': 'smart_care_events',
        'KeySchema': [
            {'AttributeName': 'event_id', 'KeyType': 'HASH'},  # Partition key
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'event_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'},
            {'AttributeName': 'resident_id', 'AttributeType': 'S'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'ResidentIdIndex',
                'KeySchema': [
                    {'AttributeName': 'resident_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'Tags': [
            {'Key': 'Project', 'Value': 'Hackathon-For-Race'},
            {'Key': 'Component', 'Value': 'SmartCareAgent'},
        ]
    },
    {
        'TableName': 'smart_care_users',
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'EmailIndex',
                'KeySchema': [
                    {'AttributeName': 'email', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'Tags': [
            {'Key': 'Project', 'Value': 'Hackathon-For-Race'},
            {'Key': 'Component', 'Value': 'SmartCareAgent'},
        ]
    },
    {
        'TableName': 'smart_care_audit_log',
        'KeySchema': [
            {'AttributeName': 'log_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'log_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'Tags': [
            {'Key': 'Project', 'Value': 'Hackathon-For-Race'},
            {'Key': 'Component', 'Value': 'SmartCareAgent'},
        ]
    }
]

def load_credentials():
    """Load AWS credentials from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

def create_dynamodb_tables():
    """Create DynamoDB tables"""
    print("=" * 70)
    print("Deploying Amazon DynamoDB Tables")
    print("=" * 70)
    
    load_credentials()
    
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    
    created_tables = []
    existing_tables = []
    
    for table_config in TABLES:
        table_name = table_config['TableName']
        
        try:
            # Check if table already exists
            try:
                response = dynamodb.describe_table(TableName=table_name)
                print(f"\n[INFO] Table '{table_name}' already exists")
                print(f"       Status: {response['Table']['TableStatus']}")
                existing_tables.append(table_name)
                continue
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            # Create the table
            print(f"\n[INFO] Creating table: {table_name}")
            response = dynamodb.create_table(**table_config)
            print(f"[OK] Table creation initiated")
            created_tables.append(table_name)
            
        except ClientError as e:
            print(f"[ERROR] Failed to create table '{table_name}': {e}")
    
    # Wait for tables to become active
    if created_tables:
        print(f"\n[INFO] Waiting for {len(created_tables)} table(s) to become active...")
        
        for table_name in created_tables:
            try:
                waiter = dynamodb.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
                print(f"[OK] Table '{table_name}' is now active")
            except ClientError as e:
                print(f"[WARNING] Error waiting for table '{table_name}': {e}")
    
    # Display summary
    print("\n" + "=" * 70)
    print("Deployment Summary")
    print("=" * 70)
    
    if created_tables:
        print(f"\n[OK] Created {len(created_tables)} table(s):")
        for table_name in created_tables:
            print(f"  - {table_name}")
    
    if existing_tables:
        print(f"\n[INFO] {len(existing_tables)} table(s) already existed:")
        for table_name in existing_tables:
            print(f"  - {table_name}")
    
    # Get table details
    print("\n" + "=" * 70)
    print("Table Details")
    print("=" * 70)
    
    all_tables = created_tables + existing_tables
    table_info = {}
    
    for table_name in all_tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            table = response['Table']
            
            print(f"\nTable: {table_name}")
            print(f"  Status: {table['TableStatus']}")
            print(f"  ARN: {table['TableArn']}")
            print(f"  Item Count: {table.get('ItemCount', 0)}")
            
            table_info[table_name] = {
                'table_name': table_name,
                'status': table['TableStatus'],
                'arn': table['TableArn'],
                'region': REGION
            }
            
        except ClientError as e:
            print(f"[ERROR] Could not describe table '{table_name}': {e}")
    
    # Save connection info
    output_file = os.path.join(os.path.dirname(__file__), '..', 'dynamodb_connection_info.json')
    with open(output_file, 'w') as f:
        json.dump({
            'region': REGION,
            'tables': table_info,
            'access_pattern': 'Use boto3.resource("dynamodb", region_name="us-west-2")'
        }, f, indent=2)
    
    print(f"\n[INFO] Connection details saved to: dynamodb_connection_info.json")
    
    return table_info

def estimate_cost():
    """Display cost estimate"""
    print("\n" + "=" * 70)
    print("Cost Estimate (Pay-per-request pricing)")
    print("=" * 70)
    print("\nDynamoDB on-demand pricing:")
    print("  - First 25 GB storage: FREE")
    print("  - Write requests: $1.25 per million")
    print("  - Read requests: $0.25 per million")
    print("\nEstimated cost for low-traffic Hackathon project:")
    print("  - ~$0-5/month (assuming < 100K requests)")
    print("\nThis is significantly cheaper than RDS MySQL (~$15-20/month)")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy DynamoDB tables for Smart Care Agent')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("Smart Care Agent - DynamoDB Deployment Script")
    print("=" * 70)
    
    estimate_cost()
    
    print("\nThis script will create 4 DynamoDB tables:")
    for table in TABLES:
        print(f"  - {table['TableName']}")
    
    if not args.yes:
        print("\nPress Ctrl+C to cancel, or Enter to continue...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n[INFO] Deployment cancelled by user")
            sys.exit(0)
    else:
        print("\n[INFO] Auto-confirming deployment (--yes flag)")

    
    # Create tables
    create_dynamodb_tables()
    
    print("\n" + "=" * 70)
    print("[OK] Deployment completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update your application to use DynamoDB SDK (boto3)")
    print("2. Implement data access layer with DynamoDB operations")
    print("3. Test CRUD operations")
    print("\nTo delete tables later:")
    print("  aws dynamodb delete-table --table-name <table-name>")
    print("=" * 70)
