"""
檢查並更新現有資料庫帳號權限
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

# 設定輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_db_connection():
    """建立資料庫連線"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ 未找到 DATABASE_URL 環境變數")
        return None
    
    # 解析 URL: mysql://user:password@host:port/database
    conn_string = database_url.replace("mysql://", "")
    user_pass, host_db = conn_string.split("@")
    username, password = user_pass.split(":")
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
        return connection
    except mysql.connector.Error as e:
        print(f"❌ 連線失敗: {e}")
        return None

def check_existing_tables(cursor):
    """檢查現有資料表"""
    print("\n" + "="*60)
    print("【檢查現有資料表】")
    print("="*60)
    
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    
    existing_tables = [table[0] for table in tables]
    
    # v2.0 新增的表
    new_tables = [
        'organizations',
        'organization_members',
        'organization_personas',
        'guardian_relationships',
        'service_principals',
        'service_permissions',
        'ai_memory_candidates',
        'ai_summary_drafts',
    ]
    
    print(f"\n總計資料表: {len(existing_tables)} 個")
    
    print("\n【v2.0 新增表狀態】")
    for table in new_tables:
        if table in existing_tables:
            print(f"  ✓ {table} - 已存在")
        else:
            print(f"  ✗ {table} - 尚未建立（需要執行 Migration）")
    
    return existing_tables, new_tables

def check_user_permissions(cursor, username, host='localhost'):
    """檢查使用者權限"""
    print(f"\n【檢查 {username}@{host} 權限】")
    
    try:
        cursor.execute(f"SHOW GRANTS FOR '{username}'@'{host}';")
        grants = cursor.fetchall()
        
        print(f"\n目前權限:")
        for grant in grants:
            print(f"  {grant[0]}")
        
        return grants
    except mysql.connector.Error as e:
        print(f"  ✗ 查詢失敗: {e}")
        return []

def grant_permissions_for_new_tables(cursor, username, new_tables, host='localhost'):
    """為新表授予權限"""
    print(f"\n【為 {username}@{host} 授予新表權限】")
    
    granted_count = 0
    failed_count = 0
    
    for table in new_tables:
        try:
            # 檢查表是否存在
            cursor.execute(f"SHOW TABLES LIKE '{table}';")
            if not cursor.fetchone():
                print(f"  ⊘ {table} - 表尚未建立，跳過")
                continue
            
            # 授予權限
            sql = f"GRANT SELECT, INSERT, UPDATE, DELETE ON smart_care_agent.{table} TO '{username}'@'{host}';"
            cursor.execute(sql)
            print(f"  ✓ {table} - 權限已授予")
            granted_count += 1
            
        except mysql.connector.Error as e:
            print(f"  ✗ {table} - 授予失敗: {e}")
            failed_count += 1
    
    # 刷新權限
    try:
        cursor.execute("FLUSH PRIVILEGES;")
        print(f"\n✓ 權限已刷新")
    except mysql.connector.Error as e:
        print(f"✗ 刷新權限失敗: {e}")
    
    return granted_count, failed_count

def check_column_exists(cursor, table, column):
    """檢查欄位是否存在"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'smart_care_agent' 
              AND TABLE_NAME = '{table}' 
              AND COLUMN_NAME = '{column}';
        """)
        count = cursor.fetchone()[0]
        return count > 0
    except:
        return False

def check_schema_updates(cursor):
    """檢查 Schema 是否已更新"""
    print("\n" + "="*60)
    print("【檢查 Schema 更新狀態】")
    print("="*60)
    
    # 檢查關鍵欄位是否已加入
    checks = [
        ('interactions', 'organization_id', '多租戶隔離'),
        ('interactions', 'actor_user_id', '操作者追蹤'),
        ('interactions', 'data_classification', '資料分類'),
        ('care_events', 'organization_id', '多租戶隔離'),
        ('care_events', 'approved_by_user_id', '核准者追蹤'),
        ('reminders', 'organization_id', '多租戶隔離'),
        ('reminders', 'timezone', '時區支援'),
        ('reminders', 'recurrence_rule', '循環提醒'),
        ('care_alerts', 'organization_id', '多租戶隔離'),
        ('daily_summaries', 'organization_id', '多租戶隔離'),
        ('personas', 'primary_organization_id', '主要機構'),
    ]
    
    updated_count = 0
    missing_count = 0
    
    print("\n【重要欄位檢查】")
    for table, column, description in checks:
        # 先檢查表是否存在
        cursor.execute(f"SHOW TABLES LIKE '{table}';")
        if not cursor.fetchone():
            print(f"  ⊘ {table}.{column} ({description}) - 表不存在")
            continue
        
        if check_column_exists(cursor, table, column):
            print(f"  ✓ {table}.{column} ({description})")
            updated_count += 1
        else:
            print(f"  ✗ {table}.{column} ({description}) - 尚未加入")
            missing_count += 1
    
    return updated_count, missing_count

def main():
    print("="*60)
    print("智慧長照系統 - 資料庫權限檢查工具")
    print("="*60)
    
    # 建立連線
    connection = get_db_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    try:
        # 1. 檢查現有資料表
        existing_tables, new_tables = check_existing_tables(cursor)
        
        # 2. 檢查 Schema 是否已更新
        updated_count, missing_count = check_schema_updates(cursor)
        
        # 3. 檢查現有帳號權限
        print("\n" + "="*60)
        print("【檢查資料庫帳號】")
        print("="*60)
        
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User LIKE 'smart_care%';")
        users = cursor.fetchall()
        
        if not users:
            print("\n✗ 未找到 smart_care 相關帳號")
            print("\n建議執行: database/setup_users.sql")
        else:
            print(f"\n找到 {len(users)} 個帳號:")
            for user, host in users:
                print(f"  • {user}@{host}")
                check_user_permissions(cursor, user, host)
        
        # 4. 詢問是否要更新權限
        print("\n" + "="*60)
        print("【權限更新】")
        print("="*60)
        
        if missing_count > 0:
            print(f"\n⚠️  偵測到 {missing_count} 個欄位尚未加入")
            print("建議先執行 Prisma Migration:")
            print("  npx prisma migrate dev --name multi_tenant_architecture")
            print("\nMigration 完成後再執行此腳本更新權限")
        else:
            print(f"\n✓ Schema 已完整更新 ({updated_count} 個欄位已確認)")
            
            # 找出需要授權的新表
            new_tables_to_grant = [t for t in new_tables if t in existing_tables]
            
            if new_tables_to_grant:
                print(f"\n發現 {len(new_tables_to_grant)} 個新表需要授權")
                
                response = input("\n是否要為 smart_care_app 授予新表權限? (y/n): ")
                
                if response.lower() == 'y':
                    granted, failed = grant_permissions_for_new_tables(
                        cursor, 
                        'smart_care_app', 
                        new_tables_to_grant
                    )
                    
                    print(f"\n✓ 完成: {granted} 個表已授權, {failed} 個失敗")
                    
                    # 再次檢查權限
                    check_user_permissions(cursor, 'smart_care_app')
                else:
                    print("\n已取消權限更新")
            else:
                print("\n✓ 所有新表權限已完整")
        
        # 5. 總結
        print("\n" + "="*60)
        print("【檢查總結】")
        print("="*60)
        print(f"\n資料表: {len(existing_tables)} 個")
        print(f"新增表: {len([t for t in new_tables if t in existing_tables])} / {len(new_tables)} 個")
        print(f"Schema 更新: {updated_count} 個欄位已確認, {missing_count} 個欄位待加入")
        
        if missing_count > 0:
            print(f"\n⚠️  下一步: 執行 Prisma Migration")
            print("  npx prisma migrate dev --name multi_tenant_architecture")
        else:
            print(f"\n✓ Schema 已完整，可以開始使用新架構")
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        connection.close()
        print("\n✓ 資料庫連線已關閉")

if __name__ == "__main__":
    main()
