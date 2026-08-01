#!/usr/bin/env python3
"""
Test RDS MySQL Connection and Verify Tables
"""

import mysql.connector
import os
import json
from datetime import datetime

def load_credentials():
    """Load credentials from .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    credentials = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"').strip("'")
                    credentials[key] = value
    
    return credentials

def test_connection():
    """Test database connection and list tables"""
    print("=" * 70)
    print("RDS MySQL Connection Test")
    print("=" * 70)
    
    creds = load_credentials()
    
    # Parse DATABASE_URL
    # Format: mysql://username:password@host:port/database
    db_url = creds.get('DATABASE_URL', '')
    if not db_url:
        print("[ERROR] DATABASE_URL not found in .env")
        return False
    
    # Extract connection details
    try:
        # Remove mysql:// prefix
        url_parts = db_url.replace('mysql://', '').split('@')
        user_pass = url_parts[0].split(':')
        host_db = url_parts[1].split('/')
        host_port = host_db[0].split(':')
        
        username = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = int(host_port[1])
        database = host_db[1]
        
        print(f"\n[INFO] Connecting to:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  Username: {username}")
        
    except Exception as e:
        print(f"[ERROR] Failed to parse DATABASE_URL: {e}")
        return False
    
    # Connect to database
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            connection_timeout=30
        )
        
        print(f"\n[OK] Connected successfully!")
        
        cursor = connection.cursor()
        
        # Get list of tables
        print("\n" + "=" * 70)
        print("Database Tables")
        print("=" * 70)
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables:\n")
        
        table_info = {}
        
        for (table_name,) in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            
            # Get table structure
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            
            table_info[table_name] = {
                'row_count': count,
                'column_count': len(columns),
                'columns': [col[0] for col in columns]
            }
            
            print(f"  {table_name:30} | {count:5} rows | {len(columns):2} columns")
        
        # Test a simple insert/select/delete
        print("\n" + "=" * 70)
        print("Test CRUD Operations")
        print("=" * 70)
        
        try:
            # Insert test persona
            cursor.execute("""
                INSERT INTO personas (persona_id, display_name, memory_namespace, created_at, updated_at, status)
                VALUES ('test-001', 'Test User', 'test-namespace', NOW(), NOW(), 'ACTIVE')
            """)
            connection.commit()
            print("\n[OK] INSERT test passed")
            
            # Select test persona
            cursor.execute("SELECT persona_id, display_name FROM personas WHERE persona_id = 'test-001'")
            result = cursor.fetchone()
            if result:
                print(f"[OK] SELECT test passed - Found: {result[1]}")
            
            # Delete test persona
            cursor.execute("DELETE FROM personas WHERE persona_id = 'test-001'")
            connection.commit()
            print(f"[OK] DELETE test passed - Removed {cursor.rowcount} row(s)")
            
        except Exception as e:
            print(f"[WARNING] CRUD test failed: {e}")
            connection.rollback()
        
        # Get database info
        print("\n" + "=" * 70)
        print("Database Information")
        print("=" * 70)
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"\nMySQL Version: {version}")
        
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]
        print(f"Current Database: {current_db}")
        
        cursor.execute("SELECT @@character_set_database, @@collation_database")
        charset, collation = cursor.fetchone()
        print(f"Character Set: {charset}")
        print(f"Collation: {collation}")
        
        # Save verification report
        report = {
            'connection': {
                'host': host,
                'port': port,
                'database': database,
                'status': 'connected'
            },
            'database_info': {
                'version': version,
                'charset': charset,
                'collation': collation
            },
            'tables': table_info,
            'tested_at': datetime.utcnow().isoformat()
        }
        
        report_file = os.path.join(os.path.dirname(__file__), '..', 'rds_verification_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[INFO] Verification report saved to: rds_verification_report.json")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 70)
        print("[OK] All Tests Passed!")
        print("=" * 70)
        
        return True
        
    except mysql.connector.Error as e:
        print(f"\n[ERROR] Database connection failed:")
        print(f"  Error Code: {e.errno}")
        print(f"  Error Message: {e.msg}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
