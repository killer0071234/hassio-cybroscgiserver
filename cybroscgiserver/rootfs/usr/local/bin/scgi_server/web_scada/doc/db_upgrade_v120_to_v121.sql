ALTER TABLE `alarms` DROP COLUMN `tag_id`;
ALTER TABLE `measurements` DROP COLUMN `tag_id`;

ALTER TABLE `alarms` MODIFY `nad` VARCHAR(12) NOT NULL;
UPDATE `alarms` SET `nad` = CONCAT('c', `nad`);

ALTER TABLE `measurements` MODIFY `nad` VARCHAR(12) NOT NULL;
UPDATE `measurements` SET `nad` = CONCAT('c', `nad`);

ALTER TABLE `controllers` MODIFY `nad` VARCHAR(12) NOT NULL;
UPDATE `controllers` SET `nad` = CONCAT('c', `nad`);

INSERT INTO `django_migrations`
VALUES (22, 'main', '0002_alter_alarm_nad_alter_alarm_timestamp_ack_and_more', '2024-11-07 16:27:43.066931');