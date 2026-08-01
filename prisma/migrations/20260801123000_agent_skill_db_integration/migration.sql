-- Durable idempotency for create_care_event.
-- Apply only after the teammate v2 schema is already present.
ALTER TABLE `care_events`
  ADD COLUMN `idempotency_key` VARCHAR(191) NULL;

CREATE UNIQUE INDEX `care_events_idempotency_key_key`
  ON `care_events`(`idempotency_key`);
