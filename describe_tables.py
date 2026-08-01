"""
輸出現有資料表詳細說明
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

def get_table_info(cursor, table_name):
    """取得資料表詳細資訊"""
    # 取得欄位資訊
    cursor.execute(f"DESCRIBE {table_name};")
    columns = cursor.fetchall()
    
    # 取得資料筆數
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    
    # 取得索引資訊
    cursor.execute(f"SHOW INDEX FROM {table_name};")
    indexes = cursor.fetchall()
    
    return {
        'columns': columns,
        'count': count,
        'indexes': indexes
    }

def get_table_description(table_name):
    """取得資料表功能說明"""
    descriptions = {
        '_prisma_migrations': {
            'name': 'Prisma Migration 元資料',
            'purpose': '記錄資料庫 Schema 版本與 Migration 歷史',
            'key_features': [
                'Migration 版本追蹤',
                'Migration 執行狀態',
                'Schema 變更歷史',
            ],
            'category': '系統管理',
        },
        'app_users': {
            'name': '後台使用者',
            'purpose': '儲存系統使用者帳號資訊（長者、家屬、機構人員、管理員）',
            'key_features': [
                '使用者名稱與密碼雜湊',
                '帳號類型（預計升級為 Enum）',
                '角色權限（預計改為細粒度）',
                '最後登入時間',
                '啟用/停用狀態',
            ],
            'category': '身分認證',
        },
        'auth_sessions': {
            'name': '登入會話',
            'purpose': '管理使用者登入 Session Token，追蹤活躍狀態',
            'key_features': [
                'Session Token 雜湊（SHA-256）',
                '過期時間管理',
                '撤銷機制（登出）',
                '最後活動時間',
            ],
            'category': '身分認證',
        },
        'personas': {
            'name': '住民主體（長者）',
            'purpose': '代表系統中的每一位長者，作為所有互動的核心主體',
            'key_features': [
                '顯示名稱與記憶命名空間',
                '偏好語言與回應風格',
                '興趣愛好（JSON）',
                '狀態管理（預計升級為 Enum）',
                '軟刪除支援',
                '【v2.0 新增】主要組織 ID',
                '【v2.0 新增】時區設定',
            ],
            'category': '核心業務',
        },
        'sessions': {
            'name': '工作階段',
            'purpose': '記錄每次對話的工作階段，管理連線生命週期',
            'key_features': [
                '關聯住民 ID（可為 null 支援匿名）',
                '階段狀態（active/expired/ended）',
                '客戶端類型與識別',
                '開始/結束/過期時間',
                '自動更新最後活動時間',
            ],
            'category': '核心業務',
        },
        'interactions': {
            'name': '互動記錄',
            'purpose': '記錄每一輪使用者輸入與 AI 回應的完整互動',
            'key_features': [
                '請求唯一識別碼（防重複提交）',
                '輸入類型（voice/text）',
                '語音識別資訊（ASR）',
                '正規化文字與 AI 回應',
                '互動狀態追蹤',
                '【v2.0 新增】組織 ID（多租戶）',
                '【v2.0 新增】操作者與服務 ID',
                '【v2.0 新增】資料分類',
            ],
            'category': '核心業務',
        },
        'tool_executions': {
            'name': '工具執行記錄',
            'purpose': 'AI 代理呼叫工具的執行歷程，連接 AI 與正式系統的橋樑',
            'key_features': [
                '工具名稱與參數（JSON）',
                '工具狀態（proposed/approved/executed）',
                '風險等級評估',
                '冪等性鍵（防重複執行）',
                '執行結果與錯誤訊息',
                '【v2.0 新增】組織 ID',
                '【v2.0 新增】服務主體 ID',
                '【v2.0 升級】9 種狀態（Enum）',
            ],
            'category': 'AI Workspace（橋接）',
        },
        'persona_preferences': {
            'name': '住民偏好（已核准記憶）',
            'purpose': '儲存長期記憶與個人偏好，支援版本控制',
            'key_features': [
                '偏好鍵值對（JSON）',
                '版本號（支援歷史追蹤）',
                '啟用/停用狀態',
                '來源類型（conversation/manual/import）',
                '來源互動 ID',
            ],
            'category': '核心業務',
        },
        'care_events': {
            'name': '照護事件（正式資料）',
            'purpose': '記錄重要照護事件，支援長期記憶管理',
            'key_features': [
                '事件類型與內容',
                '事件實際時間與結束時間',
                '信心度（AI 不確定性）',
                '記憶狀態（candidate/committed）',
                '風險等級',
                '建立者類型與 ID',
                '多時間戳記（committed/archived/deleted）',
                '【v2.0 新增】組織 ID',
                '【v2.0 新增】核准者 ID 與時間',
            ],
            'category': '核心業務',
        },
        'event_revisions': {
            'name': '事件修訂歷史',
            'purpose': '追蹤照護事件的修改歷史，確保完整稽核追蹤',
            'key_features': [
                '修訂號碼（遞增）',
                '修改前後資料（JSON）',
                '修改原因與修改者',
                '完整變更記錄',
            ],
            'category': '核心業務',
        },
        'reminders': {
            'name': '提醒排程（正式資料）',
            'purpose': '管理定時提醒與排程任務',
            'key_features': [
                '標題與描述',
                '排程時間',
                '重要性（normal/high/urgent）',
                '提醒狀態與確認狀態',
                '冪等性鍵',
                '觸發與完成時間',
                '【v2.0 新增】組織 ID',
                '【v2.0 新增】時區與循環規則',
                '【v2.0 新增】建立者與核准者',
            ],
            'category': '核心業務',
        },
        'confirmation_requests': {
            'name': '確認請求',
            'purpose': '管理需要使用者確認的操作（如高風險工具呼叫）',
            'key_features': [
                '目標類型與 ID（通用設計）',
                '確認問題',
                '確認狀態（pending/approved/rejected）',
                '過期時間',
                '使用者回應',
                '【v2.0 新增】組織與長者 ID',
                '【v2.0 新增】請求服務 ID',
                '【v2.0 新增】所需權限',
            ],
            'category': 'AI Workspace（橋接）',
        },
        'daily_summaries': {
            'name': '每日摘要（正式資料）',
            'purpose': '生成並儲存每日照護摘要報告（只儲存已核准版本）',
            'key_features': [
                '摘要日期與內容',
                '版本號（支援重新生成）',
                '審核狀態（draft/reviewed/approved）',
                '生成模型記錄',
                '【v2.0 新增】組織 ID',
            ],
            'category': '核心業務',
        },
        'daily_summary_events': {
            'name': '摘要事件關聯',
            'purpose': '連結每日摘要與相關照護事件',
            'key_features': [
                '摘要與事件關聯',
                '來源順序',
                '納入原因',
                '關聯互動 ID',
            ],
            'category': '核心業務',
        },
        'care_alerts': {
            'name': '照護警示（正式資料）',
            'purpose': '管理需要照護者注意的警示事件',
            'key_features': [
                '警示類型與嚴重程度',
                '來源文字',
                '警示狀態（open/acknowledged/resolved）',
                '指派給照護者',
                '冪等性鍵',
                '處理備註',
                '【v2.0 新增】組織 ID',
                '【v2.0 新增】確認與解決者 ID',
            ],
            'category': '核心業務',
        },
        'audit_logs': {
            'name': '稽核日誌（不可修改）',
            'purpose': '記錄所有重要操作的完整稽核追蹤',
            'key_features': [
                '請求識別碼',
                '操作者類型與 ID',
                '動作類型（create/update/delete）',
                '資源類型與 ID',
                '工具名稱（AI 操作）',
                '風險等級',
                '結果與原因',
                '額外資訊（JSON）',
                '【v2.0 新增】組織與長者 ID',
                '【v2.0 新增】服務主體 ID',
            ],
            'category': '系統管理',
        },
        'user_persona_access': {
            'name': '使用者住民存取權限',
            'purpose': '控制使用者對特定住民的存取權限（預計改為細粒度）',
            'key_features': [
                '存取等級（read/write/admin）',
                '【v2.0 升級】12 個細粒度權限欄位',
                '【v2.0 新增】組織 ID（多租戶）',
                '【v2.0 新增】授權起訖時間',
                '【v2.0 新增】撤銷機制',
            ],
            'category': '權限管理',
        },
    }
    
    return descriptions.get(table_name, {
        'name': table_name,
        'purpose': '（待補充說明）',
        'key_features': [],
        'category': '其他',
    })

def main():
    print("="*80)
    print("智慧長照系統 - 現有資料表詳細說明")
    print("="*80)
    
    connection = get_db_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    try:
        # 取得所有資料表
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\n總計: {len(tables)} 個資料表\n")
        
        # 依分類整理
        categories = {}
        for table in tables:
            desc = get_table_description(table)
            category = desc['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((table, desc))
        
        # 輸出分類統計
        print("="*80)
        print("【分類統計】")
        print("="*80)
        for category, items in categories.items():
            print(f"\n{category}: {len(items)} 個表")
            for table, desc in items:
                info = get_table_info(cursor, table)
                print(f"  • {table} ({info['count']} 筆記錄)")
        
        # 詳細輸出每個表
        print("\n" + "="*80)
        print("【詳細說明】")
        print("="*80)
        
        for category in sorted(categories.keys()):
            print(f"\n{'='*80}")
            print(f"分類: {category}")
            print("="*80)
            
            for table, desc in categories[category]:
                info = get_table_info(cursor, table)
                
                print(f"\n## {desc['name']} (`{table}`)")
                print(f"\n**用途**: {desc['purpose']}")
                print(f"\n**資料筆數**: {info['count']} 筆")
                print(f"\n**欄位數**: {len(info['columns'])} 個")
                
                if desc['key_features']:
                    print(f"\n**核心功能**:")
                    for feature in desc['key_features']:
                        if '【v2.0' in feature:
                            print(f"  🆕 {feature}")
                        else:
                            print(f"  • {feature}")
                
                print(f"\n**欄位結構**:")
                print(f"{'欄位名稱':<30} {'類型':<30} {'必填':<10} {'鍵':<10}")
                print("-" * 80)
                
                for col in info['columns']:
                    field = col[0]
                    type_ = col[1]
                    null = '✗' if col[2] == 'NO' else '✓'
                    key = col[3] if col[3] else '-'
                    
                    print(f"{field:<30} {type_:<30} {null:<10} {key:<10}")
                
                # 索引資訊
                unique_indexes = set()
                for idx in info['indexes']:
                    if idx[1] == 0:  # Non_unique = 0 表示唯一索引
                        unique_indexes.add(idx[2])  # Key_name
                
                if unique_indexes:
                    print(f"\n**唯一約束/索引**: {len(unique_indexes)} 個")
                    for idx_name in sorted(unique_indexes):
                        print(f"  • {idx_name}")
                
                print("\n" + "-"*80)
        
        # v2.0 新增表預覽
        print("\n" + "="*80)
        print("【v2.0 架構升級 - 將新增的表】")
        print("="*80)
        
        new_tables = {
            'organizations': {
                'name': '長照機構（租戶）',
                'purpose': '表示長照機構或照護服務組織，作為多租戶隔離的基礎',
                'key_features': [
                    '機構名稱與類型（6 種 Enum）',
                    '聯絡資訊與地址',
                    '時區設定',
                    '軟刪除支援',
                ],
            },
            'organization_members': {
                'name': '機構成員',
                'purpose': '記錄使用者與長照機構的隸屬關係',
                'key_features': [
                    '組織角色（6 種 Enum）',
                    '成員狀態',
                    '起訖時間',
                    '唯一約束：[organization_id + user_id]',
                ],
            },
            'organization_personas': {
                'name': '機構-長者服務關係',
                'purpose': '記錄長者與長照機構的服務關係',
                'key_features': [
                    '關係類型（primary_care/temporary/transfer）',
                    '服務狀態',
                    '服務起訖時間',
                    '支援長者轉換機構',
                    '支援一長者多機構服務',
                ],
            },
            'guardian_relationships': {
                'name': '家屬監護關係',
                'purpose': '記錄家屬、監護者與長者之間的正式授權關係',
                'key_features': [
                    '關係類型（6 種 Enum）',
                    '法定監護人標記',
                    '12 個細粒度權限欄位',
                    '授權起訖與撤銷時間',
                    '唯一約束：[user_id + persona_id + relationship_type]',
                ],
            },
            'service_principals': {
                'name': '系統服務身分',
                'purpose': '表示非人類系統身分（AI Agent、排程器、警示引擎）',
                'key_features': [
                    '服務類型（5 種 Enum）',
                    '服務描述',
                    '啟用狀態',
                    '關聯服務權限',
                ],
            },
            'service_permissions': {
                'name': '服務權限',
                'purpose': '控制系統服務可執行的操作',
                'key_features': [
                    '資源類型與動作',
                    '範圍類型',
                    '唯一約束：[service_principal_id + resource_type + action]',
                ],
            },
            'ai_memory_candidates': {
                'name': 'AI 候選記憶（AI Workspace）',
                'purpose': 'AI 從對話推論出的候選記憶，等待人工審核',
                'key_features': [
                    '記憶類型與鍵值對',
                    '候選值（JSON）',
                    '信心度',
                    '敏感度等級（4 種 Enum）',
                    '審核狀態（5 種 Enum）',
                    '審核者與審核時間',
                    '過期時間',
                ],
            },
            'ai_summary_drafts': {
                'name': 'AI 摘要草稿（AI Workspace）',
                'purpose': 'AI 產生的每日摘要或照護報告草稿，等待人工審閱',
                'key_features': [
                    '摘要日期與內容',
                    '來源事件 IDs（JSON）',
                    '生成模型與 Prompt 版本',
                    '審核狀態（6 種 Enum）',
                    '審核者與審核時間',
                ],
            },
        }
        
        print(f"\n預計新增: {len(new_tables)} 個表\n")
        
        for table, desc in new_tables.items():
            print(f"\n🆕 {desc['name']} (`{table}`)")
            print(f"   用途: {desc['purpose']}")
            print(f"   核心功能:")
            for feature in desc['key_features']:
                print(f"     • {feature}")
        
        # 既有表升級預覽
        print("\n" + "="*80)
        print("【v2.0 架構升級 - 既有表的重要變更】")
        print("="*80)
        
        upgrades = {
            'personas': [
                '+ primary_organization_id (主要機構)',
                '+ timezone (時區)',
                '✓ status 升級為 Enum（6 種狀態）',
            ],
            'app_users': [
                '✓ role 改為 account_type Enum（4 種）',
                '+ email, phone (聯絡資訊)',
                '⚠️ 機構角色改由 organization_members 管理',
            ],
            'sessions': [
                '✓ session_status 升級為 Enum（3 種）',
            ],
            'interactions': [
                '+ organization_id (多租戶隔離)',
                '+ actor_user_id (操作者)',
                '+ service_principal_id (服務 ID)',
                '+ data_classification (資料分類 Enum)',
                '✓ interaction_status 升級為 Enum（4 種）',
            ],
            'tool_executions': [
                '+ organization_id (多租戶隔離)',
                '+ service_principal_id (服務 ID)',
                '✓ tool_status 升級為 Enum（9 種狀態）',
                '✓ risk_level 升級為 Enum（4 種）',
            ],
            'care_events': [
                '+ organization_id (多租戶隔離)',
                '+ approved_by_user_id (核准者)',
                '+ approved_at (核准時間)',
                '✓ memory_status 升級為 Enum（4 種）',
                '✓ risk_level 升級為 Enum（4 種）',
                '✓ created_by_type 升級為 Enum（4 種）',
            ],
            'reminders': [
                '+ organization_id (多租戶隔離)',
                '+ timezone (時區)',
                '+ recurrence_rule (循環規則)',
                '+ risk_level (風險等級)',
                '+ created_by_type, created_by_id (建立者)',
                '+ approved_by_user_id (核准者)',
                '✓ reminder_status 升級為 Enum（4 種）',
                '✓ confirmation_status 升級為 Enum（4 種）',
            ],
            'confirmation_requests': [
                '+ organization_id, persona_id (範圍)',
                '+ requested_by_service_id (請求服務)',
                '+ required_permission (所需權限)',
                '+ confirmed_by_user_id, confirmed_at (確認資訊)',
                '✓ confirmation_status 升級為 Enum（4 種）',
            ],
            'care_alerts': [
                '+ organization_id (多租戶隔離)',
                '+ acknowledged_by_user_id, acknowledged_at (確認)',
                '+ resolved_by_user_id, resolved_at (解決)',
                '✓ alert_status 升級為 Enum（4 種）',
                '✓ severity 升級為 Enum（4 種）',
            ],
            'daily_summaries': [
                '+ organization_id (多租戶隔離)',
                '✓ review_status 升級為 Enum（6 種）',
            ],
            'user_persona_access': [
                '+ organization_id (多租戶隔離)',
                '- access_level (移除舊的 read/write/admin)',
                '+ 9 個細粒度權限欄位',
                '+ granted_by_user_id (授予者)',
                '+ starts_at, expires_at, revoked_at (時間控制)',
            ],
            'audit_logs': [
                '+ organization_id, persona_id (範圍)',
                '+ service_principal_id (服務 ID)',
                '✓ actor_type 升級為 Enum（4 種）',
                '✓ risk_level 升級為 Enum（4 種）',
            ],
        }
        
        print(f"\n預計升級: {len(upgrades)} 個既有表\n")
        
        for table, changes in upgrades.items():
            info = get_table_info(cursor, table)
            print(f"\n📝 {table} (目前 {len(info['columns'])} 個欄位, {info['count']} 筆記錄)")
            for change in changes:
                if change.startswith('+'):
                    print(f"   🆕 {change}")
                elif change.startswith('✓'):
                    print(f"   ⬆️  {change}")
                elif change.startswith('-'):
                    print(f"   ⚠️  {change}")
                elif change.startswith('⚠️'):
                    print(f"   {change}")
        
        # 總結
        print("\n" + "="*80)
        print("【總結】")
        print("="*80)
        print(f"""
v1.0 (現有架構):
  • 資料表: {len(tables)} 個
  • 資料筆數: {sum(get_table_info(cursor, t)['count'] for t in tables)} 筆
  • Enum 型別: 0 個
  • 多租戶: ❌ 無
  • 細粒度權限: ❌ 無（粗粒度 read/write/admin）
  • AI 隔離: ❌ 無

v2.0 (升級後架構):
  • 資料表: {len(tables) + len(new_tables)} 個 (+{len(new_tables)})
  • Enum 型別: 18 個
  • 多租戶: ✅ Organization-based
  • 細粒度權限: ✅ 12 個家屬權限 + 9 個機構人員權限
  • AI 隔離: ✅ AI Workspace 分離
  • 新增表: {len(new_tables)} 個
  • 升級表: {len(upgrades)} 個
  • 型別安全: ✅ 18 個 Enum 取代字串
  • 外鍵約束: ✅ 26 個新增
  • 索引優化: ✅ 18 個複合索引
        """)
        
        print("\n" + "="*80)
        print("下一步: 執行 Prisma Migration 升級到 v2.0")
        print("="*80)
        print("""
1. 備份資料庫:
   mysqldump -u root -p smart_care_agent > backup.sql

2. 執行 Migration:
   npx prisma migrate dev --name multi_tenant_v2

3. 驗證結果:
   python check_and_update_permissions.py

詳細步驟請參考: MIGRATION_GUIDE.md
        """)
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
