#!/usr/bin/env python3
"""
DynamoDB Data Access Layer for Smart Care Agent
Example implementation showing how to interact with DynamoDB tables
"""

import boto3
import os
import json
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

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

load_credentials()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

# Table references
residents_table = dynamodb.Table('smart_care_residents')
events_table = dynamodb.Table('smart_care_events')
users_table = dynamodb.Table('smart_care_users')
audit_log_table = dynamodb.Table('smart_care_audit_log')


class DynamoDBHelper:
    """Helper class to convert between Python types and DynamoDB types"""
    
    @staticmethod
    def decimal_to_float(obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: DynamoDBHelper.decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBHelper.decimal_to_float(i) for i in obj]
        return obj
    
    @staticmethod
    def float_to_decimal(obj):
        """Convert float to Decimal for DynamoDB"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: DynamoDBHelper.float_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBHelper.float_to_decimal(i) for i in obj]
        return obj


class ResidentDAO:
    """Data Access Object for Residents"""
    
    @staticmethod
    def create_resident(resident_data):
        """Create a new resident"""
        try:
            resident_data['created_at'] = int(datetime.utcnow().timestamp())
            resident_data = DynamoDBHelper.float_to_decimal(resident_data)
            
            residents_table.put_item(Item=resident_data)
            print(f"[OK] Created resident: {resident_data.get('resident_id')}")
            return resident_data
        except ClientError as e:
            print(f"[ERROR] Failed to create resident: {e}")
            return None
    
    @staticmethod
    def get_resident(resident_id):
        """Get resident by ID"""
        try:
            response = residents_table.get_item(Key={'resident_id': resident_id})
            item = response.get('Item')
            if item:
                return DynamoDBHelper.decimal_to_float(item)
            return None
        except ClientError as e:
            print(f"[ERROR] Failed to get resident: {e}")
            return None
    
    @staticmethod
    def update_resident(resident_id, updates):
        """Update resident information"""
        try:
            updates = DynamoDBHelper.float_to_decimal(updates)
            updates['updated_at'] = int(datetime.utcnow().timestamp())
            
            update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
            expression_attribute_names = {f"#{k}": k for k in updates.keys()}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}
            
            response = residents_table.update_item(
                Key={'resident_id': resident_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            return DynamoDBHelper.decimal_to_float(response.get('Attributes'))
        except ClientError as e:
            print(f"[ERROR] Failed to update resident: {e}")
            return None
    
    @staticmethod
    def list_all_residents():
        """List all residents"""
        try:
            response = residents_table.scan()
            items = response.get('Items', [])
            return [DynamoDBHelper.decimal_to_float(item) for item in items]
        except ClientError as e:
            print(f"[ERROR] Failed to list residents: {e}")
            return []


class EventDAO:
    """Data Access Object for Events"""
    
    @staticmethod
    def create_event(event_data):
        """Create a new event"""
        try:
            if 'timestamp' not in event_data:
                event_data['timestamp'] = int(datetime.utcnow().timestamp())
            
            event_data = DynamoDBHelper.float_to_decimal(event_data)
            events_table.put_item(Item=event_data)
            print(f"[OK] Created event: {event_data.get('event_id')}")
            return event_data
        except ClientError as e:
            print(f"[ERROR] Failed to create event: {e}")
            return None
    
    @staticmethod
    def get_events_by_resident(resident_id, limit=50):
        """Get events for a specific resident"""
        try:
            response = events_table.query(
                IndexName='ResidentIdIndex',
                KeyConditionExpression='resident_id = :rid',
                ExpressionAttributeValues={':rid': resident_id},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=limit
            )
            items = response.get('Items', [])
            return [DynamoDBHelper.decimal_to_float(item) for item in items]
        except ClientError as e:
            print(f"[ERROR] Failed to get events: {e}")
            return []


class UserDAO:
    """Data Access Object for Users"""
    
    @staticmethod
    def create_user(user_data):
        """Create a new user"""
        try:
            user_data['created_at'] = int(datetime.utcnow().timestamp())
            user_data = DynamoDBHelper.float_to_decimal(user_data)
            
            users_table.put_item(Item=user_data)
            print(f"[OK] Created user: {user_data.get('user_id')}")
            return user_data
        except ClientError as e:
            print(f"[ERROR] Failed to create user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        try:
            response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            items = response.get('Items', [])
            if items:
                return DynamoDBHelper.decimal_to_float(items[0])
            return None
        except ClientError as e:
            print(f"[ERROR] Failed to get user: {e}")
            return None


class AuditLogDAO:
    """Data Access Object for Audit Logs"""
    
    @staticmethod
    def log_action(log_data):
        """Create an audit log entry"""
        try:
            if 'timestamp' not in log_data:
                log_data['timestamp'] = int(datetime.utcnow().timestamp())
            
            log_data = DynamoDBHelper.float_to_decimal(log_data)
            audit_log_table.put_item(Item=log_data)
            return log_data
        except ClientError as e:
            print(f"[ERROR] Failed to create audit log: {e}")
            return None


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("DynamoDB Data Access Layer - Example Usage")
    print("=" * 70)
    
    # Example 1: Create a resident
    print("\n[Example 1] Creating a resident...")
    resident = ResidentDAO.create_resident({
        'resident_id': 'R001',
        'name': 'John Doe',
        'age': 75,
        'room_number': '101',
        'medical_conditions': ['Diabetes', 'Hypertension'],
        'emergency_contact': {
            'name': 'Jane Doe',
            'phone': '+1-555-0123',
            'relationship': 'Daughter'
        }
    })
    
    # Example 2: Get resident
    print("\n[Example 2] Retrieving resident...")
    resident = ResidentDAO.get_resident('R001')
    if resident:
        print(f"Found resident: {resident['name']}, Room: {resident['room_number']}")
    
    # Example 3: Update resident
    print("\n[Example 3] Updating resident...")
    updated = ResidentDAO.update_resident('R001', {
        'room_number': '102',
        'status': 'Active'
    })
    if updated:
        print(f"Updated room number to: {updated['room_number']}")
    
    # Example 4: Create an event
    print("\n[Example 4] Creating an event...")
    event = EventDAO.create_event({
        'event_id': f"EVT-{int(datetime.utcnow().timestamp())}",
        'resident_id': 'R001',
        'event_type': 'medication_taken',
        'description': 'Took morning medication',
        'timestamp': int(datetime.utcnow().timestamp()),
        'recorded_by': 'Nurse Smith'
    })
    
    # Example 5: Get events for resident
    print("\n[Example 5] Getting events for resident R001...")
    events = EventDAO.get_events_by_resident('R001')
    print(f"Found {len(events)} event(s)")
    for event in events:
        print(f"  - {event.get('event_type')}: {event.get('description')}")
    
    # Example 6: Create a user
    print("\n[Example 6] Creating a user...")
    user = UserDAO.create_user({
        'user_id': 'U001',
        'email': 'nurse.smith@smartcare.com',
        'name': 'Nurse Smith',
        'role': 'caregiver',
        'department': 'Nursing'
    })
    
    # Example 7: Get user by email
    print("\n[Example 7] Getting user by email...")
    user = UserDAO.get_user_by_email('nurse.smith@smartcare.com')
    if user:
        print(f"Found user: {user['name']}, Role: {user['role']}")
    
    # Example 8: Create audit log
    print("\n[Example 8] Creating audit log...")
    AuditLogDAO.log_action({
        'log_id': f"LOG-{int(datetime.utcnow().timestamp())}",
        'user_id': 'U001',
        'action': 'VIEW_RESIDENT',
        'resource_type': 'resident',
        'resource_id': 'R001',
        'ip_address': '192.168.1.100',
        'timestamp': int(datetime.utcnow().timestamp())
    })
    
    # Example 9: List all residents
    print("\n[Example 9] Listing all residents...")
    all_residents = ResidentDAO.list_all_residents()
    print(f"Total residents: {len(all_residents)}")
    for resident in all_residents:
        print(f"  - {resident['resident_id']}: {resident['name']}")
    
    print("\n" + "=" * 70)
    print("[OK] All examples completed successfully!")
    print("=" * 70)
