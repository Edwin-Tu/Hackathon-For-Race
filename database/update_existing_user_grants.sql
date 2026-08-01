-- ============================================================================
-- 檢查並更新現有資料庫帳號權限
-- ============================================================================

-- 1. 查看現有使用者
SELECT '=== 現有 smart_care 帳號 ===' AS Info;
SELECT User, Host FROM mysql.user WHERE User LIKE 'smart_care%';

-- 2. 查看現有 smart_care_app 的權限
SELECT '=== smart_care_app 目前權限 ===' AS Info;
SHOW GRANTS FOR 'smart_care_app'@'localhost';

-- 3. 查看現有 smart_care_migration 的權限（如果存在）
SELECT '=== smart_care_migration 目前權限 ===' AS Info;
SHOW GRANTS FOR 'smart_care_migration'@'localhost';

-- ============================================================================
-- 為現有 smart_care_app 帳號補充新表權限
-- ============================================================================

-- 核心租戶表
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.organizations TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.organization_members TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.organization_personas TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.guardian_relationships TO 'smart_care_app'@'localhost';

-- AI Workspace 表
GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.service_principals TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.service_permissions TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.ai_memory_candidates TO 'smart_care_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_care_agent.ai_summary_drafts TO 'smart_care_app'@'localhost';

-- 刷新權限
FLUSH PRIVILEGES;

SELECT '=== 權限更新完成 ===' AS Info;

-- 4. 再次查看更新後的權限
SELECT '=== smart_care_app 更新後權限 ===' AS Info;
SHOW GRANTS FOR 'smart_care_app'@'localhost';
