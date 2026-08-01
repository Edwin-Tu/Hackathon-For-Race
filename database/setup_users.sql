-- ============================================================================
-- Smart Care Agent Database - User Account Setup
-- 多租戶權限隔離架構 - 資料庫帳號與權限設定
-- ============================================================================
-- 版本: 2.0
-- 日期: 2026-08-01
-- 資料庫: MySQL 8.0+
-- ============================================================================

-- 注意事項:
-- 1. 請將 'YOUR_SECURE_PASSWORD_HERE' 替換為強密碼
-- 2. 根據實際部署環境調整 host (localhost / % / 特定 IP)
-- 3. 生產環境建議使用 SSL/TLS 連線
-- 4. 定期輪換密碼
-- 5. 使用環境變數儲存密碼，不要寫入版本控制

-- ============================================================================
-- 1. Migration User - 資料庫遷移專用帳號
-- ============================================================================
-- 用途: 執行 Prisma Migration、建立/修改表結構
-- 使用時機: 部署、Schema 更新
-- 風險等級: 高（有 DDL 權限）

CREATE USER IF NOT EXISTS 'smart_care_migration'@'localhost' 
IDENTIFIED BY 'YOUR_MIGRATION_PASSWORD_HERE';

-- 主資料庫權限
GRANT CREATE, ALTER, DROP, INDEX, REFERENCES
ON smart_care_agent.*
TO 'smart_care_migration'@'localhost';

-- Shadow Database 權限（Prisma Migration 需要）
GRANT ALL PRIVILEGES
ON smart_care_agent_shadow.*
TO 'smart_care_migration'@'localhost';

-- 允許查看表結構
GRANT SELECT
ON information_schema.*
TO 'smart_care_migration'@'localhost';

-- ============================================================================
-- 2. Application User - 後端應用程式專用帳號
-- ============================================================================
-- 用途: 後端 API 服務使用
-- 使用時機: 應用程式執行期間
-- 風險等級: 中（有完整 CRUD 但無 DDL）

CREATE USER IF NOT EXISTS 'smart_care_app'@'localhost' 
IDENTIFIED BY 'YOUR_APP_PASSWORD_HERE';

-- === Core Tenant & Identity Tables ===
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.organizations TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.organization_members TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.organization_personas TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.guardian_relationships TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.app_users TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.user_persona_access TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.auth_sessions TO 'smart_care_app'@'localhost';

-- === Core Business Tables ===
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.personas TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.persona_preferences TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.sessions TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.interactions TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.tool_executions TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.care_events TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.event_revisions TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.reminders TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.confirmation_requests TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.daily_summaries TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.daily_summary_events TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.care_alerts TO 'smart_care_app'@'localhost';

-- === AI Workspace Tables ===
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.service_principals TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.service_permissions TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.ai_memory_candidates TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.ai_summary_drafts TO 'smart_care_app'@'localhost';

-- === Audit Logs (只能插入和查詢，不能修改或刪除) ===
GRANT SELECT, INSERT
ON smart_care_agent.audit_logs TO 'smart_care_app'@'localhost';

-- === Prisma Migration Metadata ===
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent._prisma_migrations TO 'smart_care_app'@'localhost';

-- ============================================================================
-- 3. AI User - AI Agent 專用帳號（選用）
-- ============================================================================
-- 用途: AI Agent 直接資料庫存取（不建議，建議改用 API）
-- 使用時機: 特殊情況下 AI 需要直接查詢
-- 風險等級: 中（權限受限但有資料存取）

-- 建議: 不要讓 AI 直接連線資料庫，改用後端 API 代理
-- 如果必須使用，請取消以下註解並設定強密碼

/*
CREATE USER IF NOT EXISTS 'smart_care_ai'@'localhost' 
IDENTIFIED BY 'YOUR_AI_PASSWORD_HERE';

-- === AI Workspace 完整權限 ===
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.ai_memory_candidates TO 'smart_care_ai'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.ai_summary_drafts TO 'smart_care_ai'@'localhost';

-- === 工具執行：只能建立 PROPOSED 狀態（應用層控制） ===
GRANT SELECT, INSERT
ON smart_care_agent.tool_executions TO 'smart_care_ai'@'localhost';

-- === 確認請求：只能建立 PENDING 狀態（應用層控制） ===
GRANT SELECT, INSERT
ON smart_care_agent.confirmation_requests TO 'smart_care_ai'@'localhost';

-- === 安全讀取正式資料（建議改用 View 或 API） ===
-- 以下權限請謹慎評估後啟用
-- GRANT SELECT ON smart_care_agent.personas TO 'smart_care_ai'@'localhost';
-- GRANT SELECT ON smart_care_agent.persona_preferences TO 'smart_care_ai'@'localhost';
-- GRANT SELECT ON smart_care_agent.care_events TO 'smart_care_ai'@'localhost';
-- GRANT SELECT ON smart_care_agent.reminders TO 'smart_care_ai'@'localhost';
-- GRANT SELECT ON smart_care_agent.daily_summaries TO 'smart_care_ai'@'localhost';

-- === 明確拒絕存取敏感表 ===
-- 這些 REVOKE 是防禦性設定，即使之前未授權也執行
REVOKE ALL PRIVILEGES, GRANT OPTION
ON smart_care_agent.app_users FROM 'smart_care_ai'@'localhost';

REVOKE ALL PRIVILEGES, GRANT OPTION
ON smart_care_agent.auth_sessions FROM 'smart_care_ai'@'localhost';

REVOKE ALL PRIVILEGES, GRANT OPTION
ON smart_care_agent.audit_logs FROM 'smart_care_ai'@'localhost';

REVOKE ALL PRIVILEGES, GRANT OPTION
ON smart_care_agent.user_persona_access FROM 'smart_care_ai'@'localhost';

REVOKE ALL PRIVILEGES, GRANT OPTION
ON smart_care_agent.guardian_relationships FROM 'smart_care_ai'@'localhost';

REVOKE ALL PRIVILEGES, GRANT OPTION
ON smart_care_agent.organization_members FROM 'smart_care_ai'@'localhost';
*/

-- ============================================================================
-- 4. 刷新權限
-- ============================================================================

FLUSH PRIVILEGES;

-- ============================================================================
-- 5. 驗證帳號設定
-- ============================================================================

-- 查看已建立的使用者
SELECT User, Host FROM mysql.user 
WHERE User LIKE 'smart_care%';

-- 查看 Migration User 權限
SHOW GRANTS FOR 'smart_care_migration'@'localhost';

-- 查看 Application User 權限
SHOW GRANTS FOR 'smart_care_app'@'localhost';

-- 查看 AI User 權限（如果已建立）
-- SHOW GRANTS FOR 'smart_care_ai'@'localhost';

-- ============================================================================
-- 6. 連線字串範例
-- ============================================================================

/*
-- Migration User (只在部署時使用)
DATABASE_URL="mysql://smart_care_migration:YOUR_MIGRATION_PASSWORD_HERE@localhost:3306/smart_care_agent"

-- Application User (應用程式使用)
DATABASE_URL="mysql://smart_care_app:YOUR_APP_PASSWORD_HERE@localhost:3306/smart_care_agent"

-- AI User (如果使用直連，不建議)
AI_DATABASE_URL="mysql://smart_care_ai:YOUR_AI_PASSWORD_HERE@localhost:3306/smart_care_agent"
*/

-- ============================================================================
-- 7. 安全建議
-- ============================================================================

/*
1. 密碼強度要求:
   - 至少 16 個字元
   - 包含大小寫字母、數字、特殊符號
   - 不要使用常見單字或規律組合
   - 使用密碼生成器產生

2. 網路安全:
   -- 限制特定 IP 存取
   CREATE USER 'smart_care_app'@'192.168.1.100' IDENTIFIED BY '...';
   
   -- 啟用 SSL/TLS
   GRANT USAGE ON *.* TO 'smart_care_app'@'localhost' REQUIRE SSL;

3. 稽核與監控:
   -- 啟用 MySQL 審計日誌
   INSTALL PLUGIN audit_log SONAME 'audit_log.so';
   
   -- 監控異常查詢
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 2;

4. 定期維護:
   - 每季輪換密碼
   - 定期檢查權限變更
   - 監控異常登入嘗試
   - 備份稽核日誌

5. 應急處理:
   -- 鎖定帳號
   ALTER USER 'smart_care_ai'@'localhost' ACCOUNT LOCK;
   
   -- 解鎖帳號
   ALTER USER 'smart_care_ai'@'localhost' ACCOUNT UNLOCK;
   
   -- 撤銷所有權限
   REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'smart_care_ai'@'localhost';
   
   -- 刪除帳號
   DROP USER IF EXISTS 'smart_care_ai'@'localhost';
*/

-- ============================================================================
-- 8. 測試查詢（驗證權限隔離）
-- ============================================================================

/*
-- 測試 Application User 可以查詢業務表
-- mysql -u smart_care_app -p
USE smart_care_agent;
SELECT COUNT(*) FROM personas;  -- 應該成功
SELECT COUNT(*) FROM app_users; -- 應該成功

-- 測試 Application User 無法執行 DDL
CREATE TABLE test_table (id INT);  -- 應該失敗

-- 測試 AI User 無法查詢敏感表（如果已建立 AI User）
-- mysql -u smart_care_ai -p
USE smart_care_agent;
SELECT COUNT(*) FROM ai_memory_candidates; -- 應該成功
SELECT * FROM app_users;                   -- 應該失敗
SELECT * FROM auth_sessions;               -- 應該失敗
UPDATE audit_logs SET result = 'test';     -- 應該失敗
*/

-- ============================================================================
-- 完成
-- ============================================================================

SELECT 'Database user setup completed successfully!' AS Status;
