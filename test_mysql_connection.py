import os
import sys
import mysql.connector
from dotenv import load_dotenv

# 設定輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# 從 DATABASE_URL 解析連線資訊
database_url = os.getenv("DATABASE_URL")
print(f"Database URL: {database_url}")

# 解析 URL: mysql://user:password@host:port/database
if database_url:
    # 移除 "mysql://" 前綴
    conn_string = database_url.replace("mysql://", "")
    
    # 分割用戶資訊和主機資訊
    user_pass, host_db = conn_string.split("@")
    username, password = user_pass.split(":")
    
    # 分割主機和資料庫
    host_port, database = host_db.split("/")
    host, port = host_port.split(":")
    
    print(f"\n連線資訊:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {database}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)}")
    
    try:
        print("\n正在連線到 MySQL...")
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            database=database,
            user=username,
            password=password
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✓ 成功連線到 MySQL Server 版本: {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"✓ 當前連線的資料庫: {record[0]}")
            
            # 列出所有資料表
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            if tables:
                print(f"\n✓ 資料庫中的資料表 ({len(tables)} 個):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠ 資料庫中尚未建立資料表")
            
            cursor.close()
            
    except mysql.connector.Error as e:
        print(f"✗ 連線失敗: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n✓ MySQL 連線已關閉")
else:
    print("✗ 未找到 DATABASE_URL 環境變數")
