ALTER TABLE `auth_group` MODIFY COLUMN `name` varchar(150) NOT NULL;
ALTER TABLE `auth_permission` MODIFY COLUMN `name` varchar(255) NOT NULL;
ALTER TABLE `auth_user` MODIFY COLUMN `username` varchar(150) NOT NULL;
ALTER TABLE `auth_user` MODIFY COLUMN `first_name` varchar(150) NOT NULL;
ALTER TABLE `auth_user` MODIFY COLUMN `last_name` varchar(150) NOT NULL;
ALTER TABLE `auth_user` MODIFY COLUMN `email` varchar(254) NOT NULL;
ALTER TABLE `auth_user` MODIFY COLUMN `last_login` datetime(6) DEFAULT NULL;
ALTER TABLE `django_content_type` DROP COLUMN `name`;
ALTER TABLE `django_site` ADD UNIQUE KEY `django_site_domain_a2e37b91_uniq`(`domain`);

INSERT INTO `auth_permission`
VALUES (52, 'Can view permission', 1, 'view_permission'),
       (53, 'Can view group', 2, 'view_group'),
       (54, 'Can view user', 3, 'view_user'),
       (55, 'Can view log entry', 5, 'view_logentry'),
       (56, 'Can view content type', 6, 'view_contenttype'),
       (57, 'Can view session', 7, 'view_session'),
       (58, 'Can view site', 8, 'view_site'),
       (59, 'Can view alarm', 15, 'view_alarm'),
       (60, 'Can view measurement', 13, 'view_measurement'),
       (61, 'Can view update period', 14, 'view_updateperiod'),
       (62, 'Can view user permissions', 12, 'view_userpermissions'),
       (63, 'Can add user subscriptions', 18, 'add_usersubscriptions'),
       (64, 'Can change user subscriptions', 18, 'change_usersubscriptions'),
       (65, 'Can delete user subscriptions', 18, 'delete_usersubscriptions'),
       (66, 'Can view user subscriptions', 18, 'view_usersubscriptions'),
       (67, 'Can view custom user', 9, 'view_customuser'),
       (68, 'Can view page', 11, 'view_page'),
       (69, 'Can view plant', 17, 'view_plant'),
       (70, 'Can view controller', 16, 'view_controller'),
       (71, 'Can add relay', 19, 'add_relay'),
       (72, 'Can change relay', 19, 'change_relay'),
       (73, 'Can delete relay', 19, 'delete_relay'),
       (74, 'Can view relay', 19, 'view_relay'),
       (75, 'Can add report', 20, 'add_report'),
       (76, 'Can change report', 20, 'change_report'),
       (77, 'Can delete report', 20, 'delete_report'),
       (78, 'Can view report', 20, 'view_report'),
       (79, 'Can view template', 10, 'view_template');

INSERT INTO `django_content_type`
VALUES (18, 'main', 'usersubscriptions'),
       (19, 'main', 'relay'),
       (20, 'main', 'report');

CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `django_migrations`
VALUES (1, 'contenttypes', '0001_initial', '2024-07-05 09:13:41.413198'),
       (2, 'auth', '0001_initial', '2024-07-05 09:13:41.422275'),
       (3, 'admin', '0001_initial', '2024-07-05 09:13:41.431210'),
       (4, 'admin', '0002_logentry_remove_auto_add',
        '2024-07-05 09:13:41.436672'),
       (5, 'admin', '0003_logentry_add_action_flag_choices',
        '2024-07-05 09:13:41.440553'),
       (6, 'contenttypes', '0002_remove_content_type_name',
        '2024-07-05 09:13:41.455655'),
       (7, 'auth', '0002_alter_permission_name_max_length',
        '2024-07-05 09:13:41.463062'),
       (8, 'auth', '0003_alter_user_email_max_length',
        '2024-07-05 09:13:41.474613'),
       (9, 'auth', '0004_alter_user_username_opts',
        '2024-07-05 09:13:41.480695'),
       (10, 'auth', '0005_alter_user_last_login_null',
        '2024-07-05 09:13:41.488803'),
       (11, 'auth', '0006_require_contenttypes_0002',
        '2024-07-05 09:13:41.489619'),
       (12, 'auth', '0007_alter_validators_add_error_messages',
        '2024-07-05 09:13:41.496408'),
       (13, 'auth', '0008_alter_user_username_max_length',
        '2024-07-05 09:13:41.506431'),
       (14, 'auth', '0009_alter_user_last_name_max_length',
        '2024-07-05 09:13:41.516480'),
       (15, 'auth', '0010_alter_group_name_max_length',
        '2024-07-05 09:13:41.526310'),
       (16, 'auth', '0011_update_proxy_permissions',
        '2024-07-05 09:13:41.532062'),
       (17, 'auth', '0012_alter_user_first_name_max_length',
        '2024-07-05 09:13:41.539162'),
       (18, 'main', '0001_initial', '2024-07-05 09:13:41.614116'),
       (19, 'sessions', '0001_initial', '2024-07-05 09:13:41.616402'),
       (20, 'sites', '0001_initial', '2024-07-05 09:13:41.617945'),
       (21, 'sites', '0002_alter_domain_unique', '2024-07-05 09:13:41.622453');

UPDATE `pages` SET parent_id = NULL WHERE parent_id = '0';
UPDATE `pages` SET plant_id = NULL WHERE plant_id = '0';
UPDATE `users` SET creator_id = NULL WHERE creator_id = '0';

ALTER TABLE `templates` DROP COLUMN search_strings;
ALTER TABLE `alarms` MODIFY COLUMN tag_id int DEFAULT NULL;
ALTER TABLE `alarms` MODIFY COLUMN timestamp_gone datetime NULL;
ALTER TABLE `alarms` MODIFY COLUMN timestamp_ack datetime NULL;
