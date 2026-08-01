import os
import sys
import mysql.connector
from dotenv import load_dotenv

# 設定輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# 從 DATABASE_URL 解析連線資訊
database_url = os.getenv("DATABASE_URL")

if database_url:
    # 移除 "mysql://" 前綴
    conn_string = database_url.replace("mysql://", "")
    
    # 分割用戶資訊和主機資訊
    user_pass, host_db = conn_string.split("@")
    username, password = user_pass.split(":")
    
    # 分割主機和資料庫
    host_port, database = host_db.split("/")
    host, port = host_port.split(":")
    
    try:
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            database=database,
            user=username,
            password=password
        )
        
        if connection.is_connected():
            print("=" * 60)
            print("MySQL 連線測試報告")
            print("=" * 60)
            
            cursor = connection.cursor()
            
            # 1. 伺服器資訊
            print(f"\n【伺服器資訊】")
            print(f"  MySQL 版本: {connection.server_info}")
            print(f"  主機: {host}:{port}")
            print(f"  資料庫: {database}")
            print(f"  使用者: {username}")
            
            # 2. 資料表統計
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"\n【資料表統計】")
            print(f"  總計: {len(tables)} 個資料表")
            
            # 3. 檢查核心資料表結構
            core_tables = ['personas', 'sessions', 'interactions', 'care_events']
            print(f"\n【核心資料表驗證】")
            
            for table_name in core_tables:
                cursor.execute(f"DESCRIBE {table_name};")
                columns = cursor.fetchall()
                print(f"\n  ✓ {table_name} ({len(columns)} 個欄位)")
                for col in columns[:5]:  # 只顯示前5個欄位
                    print(f"    - {col[0]}: {col[1]}")
                if len(columns) > 5:
                    print(f"    ... 還有 {len(columns) - 5} 個欄位")
            
            # 4. 檢查資料表記錄數
            print(f"\n【資料表記錄數】")
            for table in tables:
                table_name = table[0]
                if table_name != '_prisma_migrations':
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"  {table_name}: {count} 筆記錄")
            
            # 5. 檢查 Prisma Migrations
            cursor.execute("SELECT migration_name, finished_at FROM _prisma_migrations ORDER BY finished_at DESC LIMIT 5;")
            migrations = cursor.fetchall()
            print(f"\n【Prisma Migrations】")
            for migration in migrations:
                print(f"  ✓ {migration[0]}")
                print(f"    完成時間: {migration[1]}")
            
            cursor.close()
            print("\n" + "=" * 60)
            print("✓ MySQL 連線測試成功完成")
            print("=" * 60)
            
    except mysql.connector.Error as e:
        print(f"✗ 連線失敗: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
else:
    print("✗ 未找到 DATABASE_URL 環境變數")
