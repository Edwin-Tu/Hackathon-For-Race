-- CreateTable
CREATE TABLE `personas` (
  `persona_id` VARCHAR(191) NOT NULL,
  `display_name` VARCHAR(191) NOT NULL,
  `memory_namespace` VARCHAR(191) NOT NULL,
  `preferred_language` VARCHAR(191) NOT NULL DEFAULT 'zh-TW',
  `response_style` VARCHAR(191) NULL,
  `response_style_config` JSON NULL,
  `interests` JSON NULL,
  `status` VARCHAR(191) NOT NULL DEFAULT 'active',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,
  `deleted_at` DATETIME(3) NULL,

  UNIQUE INDEX `personas_memory_namespace_key` (`memory_namespace`),
  PRIMARY KEY (`persona_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `sessions` (
  `session_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NULL,
  `session_status` VARCHAR(191) NOT NULL DEFAULT 'active',
  `client_type` VARCHAR(191) NOT NULL,
  `client_identifier` VARCHAR(191) NULL,
  `started_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `last_active_at` DATETIME(3) NOT NULL,
  `expires_at` DATETIME(3) NULL,
  `ended_at` DATETIME(3) NULL,
  `end_reason` VARCHAR(191) NULL,

  PRIMARY KEY (`session_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `interactions` (
  `interaction_id` VARCHAR(191) NOT NULL,
  `request_id` VARCHAR(191) NOT NULL,
  `session_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `input_type` VARCHAR(191) NOT NULL,
  `transcript` TEXT NULL,
  `normalized_text` TEXT NULL,
  `asr_language` VARCHAR(191) NULL,
  `asr_confidence` DOUBLE NULL,
  `asr_metadata` JSON NULL,
  `agent_response` TEXT NULL,
  `interaction_status` VARCHAR(191) NOT NULL DEFAULT 'received',
  `error_code` VARCHAR(191) NULL,
  `error_message` VARCHAR(191) NULL,
  `started_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `completed_at` DATETIME(3) NULL,

  UNIQUE INDEX `interactions_request_id_key` (`request_id`),
  PRIMARY KEY (`interaction_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `tool_executions` (
  `tool_execution_id` VARCHAR(191) NOT NULL,
  `request_id` VARCHAR(191) NOT NULL,
  `session_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `interaction_id` VARCHAR(191) NULL,
  `tool_name` VARCHAR(191) NOT NULL,
  `tool_arguments` JSON NOT NULL,
  `tool_status` VARCHAR(191) NOT NULL DEFAULT 'proposed',
  `risk_level` VARCHAR(191) NULL,
  `idempotency_key` VARCHAR(191) NULL,
  `record_type` VARCHAR(191) NULL,
  `record_id` VARCHAR(191) NULL,
  `result_payload` JSON NULL,
  `error_code` VARCHAR(191) NULL,
  `error_message` VARCHAR(191) NULL,
  `started_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `finished_at` DATETIME(3) NULL,

  UNIQUE INDEX `tool_executions_idempotency_key_key` (`idempotency_key`),
  PRIMARY KEY (`tool_execution_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `persona_preferences` (
  `preference_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `preference_key` VARCHAR(191) NOT NULL,
  `preference_value` JSON NOT NULL,
  `version` INTEGER NOT NULL DEFAULT 1,
  `is_active` BOOLEAN NOT NULL DEFAULT true,
  `source_type` VARCHAR(191) NOT NULL,
  `source_interaction_id` VARCHAR(191) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  UNIQUE INDEX `persona_preferences_persona_id_preference_key_version_key` (`persona_id`, `preference_key`, `version`),
  PRIMARY KEY (`preference_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `care_events` (
  `event_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `session_id` VARCHAR(191) NULL,
  `interaction_id` VARCHAR(191) NULL,
  `tool_execution_id` VARCHAR(191) NULL,
  `event_type` VARCHAR(191) NOT NULL,
  `content` TEXT NOT NULL,
  `event_time` DATETIME(3) NULL,
  `event_end_time` DATETIME(3) NULL,
  `confidence` DOUBLE NULL,
  `source_text` TEXT NULL,
  `memory_status` VARCHAR(191) NOT NULL DEFAULT 'candidate',
  `risk_level` VARCHAR(191) NULL,
  `created_by_type` VARCHAR(191) NULL,
  `created_by_id` VARCHAR(191) NULL,
  `committed_at` DATETIME(3) NULL,
  `archived_at` DATETIME(3) NULL,
  `deleted_at` DATETIME(3) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  PRIMARY KEY (`event_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `event_revisions` (
  `revision_id` VARCHAR(191) NOT NULL,
  `event_id` VARCHAR(191) NOT NULL,
  `revision_number` INTEGER NOT NULL,
  `old_data` JSON NULL,
  `new_data` JSON NULL,
  `change_reason` VARCHAR(191) NULL,
  `changed_by` VARCHAR(191) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

  UNIQUE INDEX `event_revisions_event_id_revision_number_key` (`event_id`, `revision_number`),
  PRIMARY KEY (`revision_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `reminders` (
  `reminder_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `interaction_id` VARCHAR(191) NULL,
  `title` VARCHAR(191) NOT NULL,
  `description` TEXT NULL,
  `scheduled_at` DATETIME(3) NOT NULL,
  `importance` VARCHAR(191) NOT NULL DEFAULT 'normal',
  `reminder_status` VARCHAR(191) NOT NULL DEFAULT 'scheduled',
  `confirmation_status` VARCHAR(191) NULL DEFAULT 'pending',
  `idempotency_key` VARCHAR(191) NULL,
  `triggered_at` DATETIME(3) NULL,
  `completed_at` DATETIME(3) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  UNIQUE INDEX `reminders_idempotency_key_key` (`idempotency_key`),
  PRIMARY KEY (`reminder_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `confirmation_requests` (
  `confirmation_id` VARCHAR(191) NOT NULL,
  `session_id` VARCHAR(191) NOT NULL,
  `target_type` VARCHAR(191) NOT NULL,
  `target_id` VARCHAR(191) NOT NULL,
  `confirmation_question` VARCHAR(191) NOT NULL,
  `confirmation_status` VARCHAR(191) NOT NULL DEFAULT 'pending',
  `expires_at` DATETIME(3) NULL,
  `response_text` VARCHAR(191) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  PRIMARY KEY (`confirmation_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `daily_summaries` (
  `summary_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `summary_date` DATETIME(3) NOT NULL,
  `summary_text` TEXT NOT NULL,
  `summary_version` INTEGER NOT NULL DEFAULT 1,
  `review_status` VARCHAR(191) NOT NULL DEFAULT 'draft',
  `generation_model` VARCHAR(191) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  PRIMARY KEY (`summary_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `daily_summary_events` (
  `summary_id` VARCHAR(191) NOT NULL,
  `event_id` VARCHAR(191) NOT NULL,
  `source_order` INTEGER NOT NULL,
  `included_reason` VARCHAR(191) NULL,
  `interaction_id` VARCHAR(191) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

  PRIMARY KEY (`summary_id`, `event_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `care_alerts` (
  `alert_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `alert_type` VARCHAR(191) NOT NULL,
  `severity` VARCHAR(191) NOT NULL,
  `source_text` TEXT NULL,
  `alert_status` VARCHAR(191) NOT NULL DEFAULT 'open',
  `assigned_to` VARCHAR(191) NULL,
  `idempotency_key` VARCHAR(191) NULL,
  `resolution_note` TEXT NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  UNIQUE INDEX `care_alerts_idempotency_key_key` (`idempotency_key`),
  PRIMARY KEY (`alert_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `audit_logs` (
  `audit_id` VARCHAR(191) NOT NULL,
  `request_id` VARCHAR(191) NOT NULL,
  `actor_type` VARCHAR(191) NOT NULL,
  `action_type` VARCHAR(191) NOT NULL,
  `resource_type` VARCHAR(191) NOT NULL,
  `resource_id` VARCHAR(191) NULL,
  `tool_name` VARCHAR(191) NULL,
  `risk_level` VARCHAR(191) NULL,
  `result` VARCHAR(191) NOT NULL,
  `reason` TEXT NULL,
  `metadata` JSON NULL,
  `persona_id` VARCHAR(191) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

  PRIMARY KEY (`audit_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `app_users` (
  `user_id` VARCHAR(191) NOT NULL,
  `username` VARCHAR(191) NOT NULL,
  `password_hash` VARCHAR(191) NOT NULL,
  `display_name` VARCHAR(191) NOT NULL,
  `role` VARCHAR(191) NOT NULL DEFAULT 'caregiver',
  `persona_id` VARCHAR(191) NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT true,
  `last_login_at` DATETIME(3) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL,

  UNIQUE INDEX `app_users_username_key` (`username`),
  PRIMARY KEY (`user_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `user_persona_access` (
  `access_id` VARCHAR(191) NOT NULL,
  `user_id` VARCHAR(191) NOT NULL,
  `persona_id` VARCHAR(191) NOT NULL,
  `access_level` VARCHAR(191) NOT NULL DEFAULT 'read',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

  UNIQUE INDEX `user_persona_access_user_id_persona_id_key` (`user_id`, `persona_id`),
  PRIMARY KEY (`access_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `auth_sessions` (
  `session_token_hash` VARCHAR(191) NOT NULL,
  `user_id` VARCHAR(191) NOT NULL,
  `expires_at` DATETIME(3) NOT NULL,
  `revoked_at` DATETIME(3) NULL,
  `last_seen_at` DATETIME(3) NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

  PRIMARY KEY (`session_token_hash`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `sessions`
  ADD CONSTRAINT `sessions_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `interactions`
  ADD CONSTRAINT `interactions_session_id_fkey` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `interactions`
  ADD CONSTRAINT `interactions_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `tool_executions`
  ADD CONSTRAINT `tool_executions_interaction_id_fkey` FOREIGN KEY (`interaction_id`) REFERENCES `interactions` (`interaction_id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `persona_preferences`
  ADD CONSTRAINT `persona_preferences_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `care_events`
  ADD CONSTRAINT `care_events_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `care_events`
  ADD CONSTRAINT `care_events_interaction_id_fkey` FOREIGN KEY (`interaction_id`) REFERENCES `interactions` (`interaction_id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `event_revisions`
  ADD CONSTRAINT `event_revisions_event_id_fkey` FOREIGN KEY (`event_id`) REFERENCES `care_events` (`event_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `reminders`
  ADD CONSTRAINT `reminders_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `reminders`
  ADD CONSTRAINT `reminders_interaction_id_fkey` FOREIGN KEY (`interaction_id`) REFERENCES `interactions` (`interaction_id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `confirmation_requests`
  ADD CONSTRAINT `confirmation_requests_session_id_fkey` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `daily_summaries`
  ADD CONSTRAINT `daily_summaries_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `daily_summary_events`
  ADD CONSTRAINT `daily_summary_events_summary_id_fkey` FOREIGN KEY (`summary_id`) REFERENCES `daily_summaries` (`summary_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `daily_summary_events`
  ADD CONSTRAINT `daily_summary_events_interaction_id_fkey` FOREIGN KEY (`interaction_id`) REFERENCES `interactions` (`interaction_id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `care_alerts`
  ADD CONSTRAINT `care_alerts_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `audit_logs`
  ADD CONSTRAINT `audit_logs_persona_id_fkey` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`persona_id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `user_persona_access`
  ADD CONSTRAINT `user_persona_access_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `app_users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `auth_sessions`
  ADD CONSTRAINT `auth_sessions_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `app_users` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE;
