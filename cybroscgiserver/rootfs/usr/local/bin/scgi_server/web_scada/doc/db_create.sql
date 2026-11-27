-- phpMyAdmin SQL Dump
-- version 5.2.1deb3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Nov 21, 2024 at 12:59 PM
-- Server version: 10.11.8-MariaDB-0ubuntu0.24.04.1
-- PHP Version: 8.3.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `solar`
--
USE `solar`;

-- --------------------------------------------------------

--
-- Table structure for table `alarms`
--

DROP TABLE IF EXISTS `alarms`;
CREATE TABLE `alarms` (
  `id` int(11) NOT NULL,
  `type` int(11) NOT NULL,
  `nad` varchar(12) NOT NULL,
  `priority` tinyint(4) NOT NULL,
  `tag` varchar(40) NOT NULL,
  `value` varchar(16) NOT NULL,
  `class` varchar(20) NOT NULL,
  `message` varchar(50) NOT NULL,
  `timestamp_raise` datetime NOT NULL,
  `timestamp_gone` datetime DEFAULT NULL,
  `timestamp_ack` datetime DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `date_joined` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `controllers`
--

DROP TABLE IF EXISTS `controllers`;
CREATE TABLE `controllers` (
  `id` int(11) NOT NULL,
  `nad` varchar(12) NOT NULL,
  `location` varchar(50) NOT NULL,
  `function` varchar(1000) NOT NULL,
  `created_id` int(11) DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `plant_id` int(11) DEFAULT NULL,
  `active` tinyint(1) NOT NULL,
  `connection_type` int(11) NOT NULL DEFAULT 0,
  `password` varchar(30) NOT NULL DEFAULT '',
  `comm_status` int(11) NOT NULL DEFAULT 0,
  `date_added` datetime NOT NULL,
  `last_modified` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `countries`
--

DROP TABLE IF EXISTS `countries`;
CREATE TABLE `countries` (
  `id` int(10) UNSIGNED NOT NULL,
  `iso` varchar(45) DEFAULT NULL,
  `iso3` varchar(45) DEFAULT NULL,
  `fips` varchar(45) DEFAULT NULL,
  `name` varchar(45) DEFAULT NULL,
  `continent` varchar(45) DEFAULT NULL,
  `currency_code` varchar(45) DEFAULT NULL,
  `currency_name` varchar(45) DEFAULT NULL,
  `phone_prefix` varchar(45) DEFAULT NULL,
  `postal_code` varchar(45) DEFAULT NULL,
  `languages` varchar(45) DEFAULT NULL,
  `geonameid` int(11) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `datalogger_tags`
--

DROP TABLE IF EXISTS `datalogger_tags`;
CREATE TABLE `datalogger_tags` (
  `id` int(11) NOT NULL,
  `tag_id` int(11) DEFAULT NULL,
  `type` smallint(6) NOT NULL,
  `priority` smallint(6) NOT NULL,
  `message` varchar(50) NOT NULL,
  `class` varchar(20) NOT NULL,
  `order` int(11) NOT NULL,
  `enabled` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL,
  `change_message` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `measurements`
--

DROP TABLE IF EXISTS `measurements`;
CREATE TABLE `measurements` (
  `id` int(11) NOT NULL,
  `nad` varchar(12) NOT NULL,
  `tag` varchar(40) NOT NULL,
  `value` varchar(16) NOT NULL,
  `timestamp` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `pages`
--

DROP TABLE IF EXISTS `pages`;
CREATE TABLE `pages` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(1000) NOT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `plant_id` int(11) DEFAULT NULL,
  `path` varchar(200) NOT NULL,
  `data_folder` varchar(200) NOT NULL,
  `content` longtext NOT NULL,
  `author_id` int(11) DEFAULT NULL,
  `modified_by_id` int(11) DEFAULT NULL,
  `order` int(11) NOT NULL,
  `update_period_id` int(11) DEFAULT NULL,
  `separator` tinyint(1) NOT NULL DEFAULT 0,
  `public` tinyint(1) NOT NULL,
  `published` tinyint(1) NOT NULL,
  `date_added` datetime NOT NULL,
  `last_modified` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
CREATE TABLE `permissions` (
  `id` int(11) NOT NULL,
  `is_server_admin` tinyint(1) NOT NULL,
  `can_manage_plants` tinyint(1) NOT NULL,
  `can_manage_users` tinyint(1) NOT NULL,
  `can_manage_templates` tinyint(1) NOT NULL,
  `can_manage_controllers` tinyint(1) NOT NULL,
  `can_manage_media` tinyint(1) NOT NULL,
  `can_manage_site_content` tinyint(1) NOT NULL,
  `rw_tags_access` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `plants`
--

DROP TABLE IF EXISTS `plants`;
CREATE TABLE `plants` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(1000) NOT NULL,
  `commission_date` varchar(20) DEFAULT NULL,
  `author_id` int(11) DEFAULT NULL,
  `modified_by_id` int(11) DEFAULT NULL,
  `order` int(11) NOT NULL,
  `homepage_id` int(11) DEFAULT NULL,
  `public` tinyint(1) NOT NULL,
  `nominal_power` double NOT NULL DEFAULT 0,
  `city` varchar(100) NOT NULL DEFAULT '',
  `country_id` int(11) DEFAULT NULL,
  `region_id` int(11) DEFAULT NULL,
  `latitude` double NOT NULL DEFAULT 0,
  `longitude` double NOT NULL DEFAULT 0,
  `photo` varchar(100) NOT NULL DEFAULT '',
  `photo_thumb` varchar(100) NOT NULL DEFAULT '',
  `url` varchar(100) NOT NULL DEFAULT '',
  `status` int(11) NOT NULL DEFAULT 0,
  `comm_status` int(11) NOT NULL DEFAULT 0,
  `current_power_tag_id` int(11) DEFAULT NULL,
  `total_energy_tag_id` int(11) DEFAULT NULL,
  `datalogger_tags_changed` tinyint(1) NOT NULL DEFAULT 0,
  `date_added` datetime NOT NULL,
  `last_modified` datetime NOT NULL,
  `timezone` varchar(64) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `plants_admins`
--

DROP TABLE IF EXISTS `plants_admins`;
CREATE TABLE `plants_admins` (
  `id` int(11) NOT NULL,
  `plant_id` int(11) NOT NULL,
  `customuser_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `plants_users`
--

DROP TABLE IF EXISTS `plants_users`;
CREATE TABLE `plants_users` (
  `id` int(11) NOT NULL,
  `plant_id` int(11) NOT NULL,
  `customuser_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `regions`
--

DROP TABLE IF EXISTS `regions`;
CREATE TABLE `regions` (
  `id` int(10) UNSIGNED NOT NULL,
  `country_id` int(10) UNSIGNED DEFAULT NULL,
  `name` varchar(45) DEFAULT NULL,
  `timezone` varchar(45) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `relays`
--

DROP TABLE IF EXISTS `relays`;
CREATE TABLE `relays` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `session_id` int(11) UNSIGNED NOT NULL,
  `message_count_tx` int(11) NOT NULL,
  `message_count_rx` int(11) NOT NULL,
  `last_message` datetime DEFAULT NULL,
  `last_controller_nad` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

DROP TABLE IF EXISTS `reports`;
CREATE TABLE `reports` (
  `id` int(11) NOT NULL,
  `plant_id` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  `type` int(11) NOT NULL,
  `timestamp_sent` datetime DEFAULT NULL,
  `report_text` text DEFAULT NULL,
  `report_html` text DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `subscriptions`
--

DROP TABLE IF EXISTS `subscriptions`;
CREATE TABLE `subscriptions` (
  `id` int(11) NOT NULL,
  `alarms_events_subscription` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
CREATE TABLE `tags` (
  `id` int(11) NOT NULL,
  `controller_id` int(11) DEFAULT NULL,
  `nad` smallint(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `address` int(11) NOT NULL,
  `tag_id` int(11) DEFAULT NULL,
  `array_size` smallint(6) NOT NULL,
  `is_array` tinyint(1) NOT NULL,
  `offset` int(11) NOT NULL,
  `size` smallint(6) NOT NULL,
  `scope` smallint(6) NOT NULL,
  `type` smallint(6) NOT NULL,
  `description` varchar(255) NOT NULL,
  `valid` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `templates`
--

DROP TABLE IF EXISTS `templates`;
CREATE TABLE `templates` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `plant_id` int(11) DEFAULT NULL,
  `content` longtext NOT NULL,
  `author_id` int(11) DEFAULT NULL,
  `modified_by_id` int(11) DEFAULT NULL,
  `order` int(11) NOT NULL,
  `published` tinyint(1) NOT NULL,
  `date_added` datetime NOT NULL,
  `last_modified` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `time_zone`
--

DROP TABLE IF EXISTS `time_zone`;
CREATE TABLE `time_zone` (
  `Time_zone_id` int(10) UNSIGNED NOT NULL,
  `Use_leap_seconds` enum('Y','N') NOT NULL DEFAULT 'N'
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci COMMENT='Time zones';

-- --------------------------------------------------------

--
-- Table structure for table `time_zone_leap_second`
--

DROP TABLE IF EXISTS `time_zone_leap_second`;
CREATE TABLE `time_zone_leap_second` (
  `Transition_time` bigint(20) NOT NULL DEFAULT 0,
  `Correction` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci COMMENT='Leap seconds information for time zones';

-- --------------------------------------------------------

--
-- Table structure for table `time_zone_name`
--

DROP TABLE IF EXISTS `time_zone_name`;
CREATE TABLE `time_zone_name` (
  `Name` char(64) NOT NULL DEFAULT '',
  `Time_zone_id` int(10) UNSIGNED NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci COMMENT='Time zone names';

-- --------------------------------------------------------

--
-- Table structure for table `time_zone_transition`
--

DROP TABLE IF EXISTS `time_zone_transition`;
CREATE TABLE `time_zone_transition` (
  `Time_zone_id` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `Transition_time` bigint(20) NOT NULL DEFAULT 0,
  `Transition_type_id` int(10) UNSIGNED NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci COMMENT='Time zone transitions';

-- --------------------------------------------------------

--
-- Table structure for table `time_zone_transition_type`
--

DROP TABLE IF EXISTS `time_zone_transition_type`;
CREATE TABLE `time_zone_transition_type` (
  `Time_zone_id` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `Transition_type_id` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `Offset` int(11) NOT NULL DEFAULT 0,
  `Is_DST` tinyint(3) UNSIGNED NOT NULL DEFAULT 0,
  `Abbreviation` char(8) NOT NULL DEFAULT ''
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci COMMENT='Time zone transition types';

-- --------------------------------------------------------

--
-- Table structure for table `updateperiods`
--

DROP TABLE IF EXISTS `updateperiods`;
CREATE TABLE `updateperiods` (
  `id` int(11) NOT NULL,
  `text` varchar(10) NOT NULL,
  `period` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_ptr_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `login_count` int(11) NOT NULL,
  `permissions_id` int(11) NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `last_ip` char(15) NOT NULL,
  `subscriptions_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users_homepages`
--

DROP TABLE IF EXISTS `users_homepages`;
CREATE TABLE `users_homepages` (
  `id` int(11) NOT NULL,
  `customuser_id` int(11) NOT NULL,
  `page_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `writetag_log`
--

DROP TABLE IF EXISTS `writetag_log`;
CREATE TABLE `writetag_log` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `plant_id` int(11) DEFAULT NULL,
  `controller_id` int(11) DEFAULT NULL,
  `tag` varchar(50) NOT NULL,
  `page_id` int(11) DEFAULT NULL,
  `new_value` varchar(16) NOT NULL,
  `rejected` tinyint(1) NOT NULL,
  `timestamp` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `alarms`
--
ALTER TABLE `alarms`
  ADD PRIMARY KEY (`id`),
  ADD KEY `tag_index` (`tag`);

--
-- Indexes for table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  ADD KEY `permission_id_refs_id_a7792de1` (`permission_id`);

--
-- Indexes for table `auth_message`
--
ALTER TABLE `auth_message`
  ADD PRIMARY KEY (`id`),
  ADD KEY `auth_message_user_id` (`user_id`);

--
-- Indexes for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  ADD KEY `auth_permission_content_type_id` (`content_type_id`);

--
-- Indexes for table `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`group_id`),
  ADD KEY `group_id_refs_id_f0ee9890` (`group_id`);

--
-- Indexes for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  ADD KEY `permission_id_refs_id_67e79cb` (`permission_id`);

--
-- Indexes for table `controllers`
--
ALTER TABLE `controllers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nad_index` (`nad`),
  ADD KEY `controllers_created_id` (`created_id`),
  ADD KEY `controllers_owner_id` (`owner_id`),
  ADD KEY `controllers_plant_id` (`plant_id`),
  ADD KEY `plant_id_refs_id_9918366d` (`plant_id`),
  ADD KEY `owner_id_refs_user_ptr_id_7e341e7c` (`owner_id`),
  ADD KEY `created_id_refs_user_ptr_id_7e341e7c` (`created_id`);

--
-- Indexes for table `countries`
--
ALTER TABLE `countries`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `datalogger_tags`
--
ALTER TABLE `datalogger_tags`
  ADD PRIMARY KEY (`id`),
  ADD KEY `datalogger_tags_3747b463` (`tag_id`);

--
-- Indexes for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_user_id` (`user_id`),
  ADD KEY `django_admin_log_content_type_id` (`content_type_id`);

--
-- Indexes for table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `app_label` (`app_label`,`model`);

--
-- Indexes for table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`);

--
-- Indexes for table `django_site`
--
ALTER TABLE `django_site`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_site_domain_a2e37b91_uniq` (`domain`);

--
-- Indexes for table `measurements`
--
ALTER TABLE `measurements`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tag_timestamp_index` (`tag`,`timestamp`);

--
-- Indexes for table `pages`
--
ALTER TABLE `pages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `pages_parent_id` (`parent_id`),
  ADD KEY `pages_plant_id` (`plant_id`),
  ADD KEY `pages_author_id` (`author_id`),
  ADD KEY `pages_update_period_id` (`update_period_id`),
  ADD KEY `modified_by_id_refs_user_ptr_id_d65b5c83` (`modified_by_id`),
  ADD KEY `plant_id_refs_id_8cb21e6e` (`plant_id`),
  ADD KEY `update_period_id_refs_id_9ad09da0` (`update_period_id`),
  ADD KEY `parent_id_refs_id_3067db9b` (`parent_id`),
  ADD KEY `author_id_refs_user_ptr_id_d65b5c83` (`author_id`);

--
-- Indexes for table `permissions`
--
ALTER TABLE `permissions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `plants`
--
ALTER TABLE `plants`
  ADD PRIMARY KEY (`id`),
  ADD KEY `plants_author_id` (`author_id`),
  ADD KEY `plants_homepage_id` (`homepage_id`),
  ADD KEY `modified_by_id_refs_user_ptr_id_36590f74` (`modified_by_id`),
  ADD KEY `country_id_refs_id_a1057b32` (`country_id`),
  ADD KEY `region_id_refs_id_513fdced` (`region_id`),
  ADD KEY `current_power_tag_id_refs_id_90c963ae` (`current_power_tag_id`),
  ADD KEY `total_energy_tag_id_refs_id_90c963ae` (`total_energy_tag_id`),
  ADD KEY `author_id_refs_user_ptr_id_36590f74` (`author_id`),
  ADD KEY `homepage_id_refs_id_fa444fa4` (`homepage_id`);

--
-- Indexes for table `plants_admins`
--
ALTER TABLE `plants_admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `plant_id` (`plant_id`,`customuser_id`),
  ADD KEY `customuser_id_refs_user_ptr_id_22ec05f4` (`customuser_id`);

--
-- Indexes for table `plants_users`
--
ALTER TABLE `plants_users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `plant_id` (`plant_id`,`customuser_id`),
  ADD KEY `customuser_id_refs_user_ptr_id_a22c2129` (`customuser_id`);

--
-- Indexes for table `regions`
--
ALTER TABLE `regions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `country_id_refs_id_ce363f62` (`country_id`);

--
-- Indexes for table `relays`
--
ALTER TABLE `relays`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id_refs_user_ptr_id_2c1e7d40` (`user_id`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `reports_plant_id` (`plant_id`),
  ADD KEY `reports_index` (`plant_id`,`type`,`timestamp`);

--
-- Indexes for table `subscriptions`
--
ALTER TABLE `subscriptions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tags`
--
ALTER TABLE `tags`
  ADD PRIMARY KEY (`id`),
  ADD KEY `tags_a0221886` (`controller_id`),
  ADD KEY `name_index` (`name`);

--
-- Indexes for table `templates`
--
ALTER TABLE `templates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `templates_author_id` (`author_id`),
  ADD KEY `modified_by_id_refs_user_ptr_id_1f1807ac` (`modified_by_id`),
  ADD KEY `plant_id_refs_id_1b964523` (`plant_id`),
  ADD KEY `author_id_refs_user_ptr_id_1f1807ac` (`author_id`);

--
-- Indexes for table `time_zone`
--
ALTER TABLE `time_zone`
  ADD PRIMARY KEY (`Time_zone_id`);

--
-- Indexes for table `time_zone_leap_second`
--
ALTER TABLE `time_zone_leap_second`
  ADD PRIMARY KEY (`Transition_time`);

--
-- Indexes for table `time_zone_name`
--
ALTER TABLE `time_zone_name`
  ADD PRIMARY KEY (`Name`);

--
-- Indexes for table `time_zone_transition`
--
ALTER TABLE `time_zone_transition`
  ADD PRIMARY KEY (`Time_zone_id`,`Transition_time`);

--
-- Indexes for table `time_zone_transition_type`
--
ALTER TABLE `time_zone_transition_type`
  ADD PRIMARY KEY (`Time_zone_id`,`Transition_type_id`);

--
-- Indexes for table `updateperiods`
--
ALTER TABLE `updateperiods`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_ptr_id`),
  ADD UNIQUE KEY `permissions_id` (`permissions_id`),
  ADD UNIQUE KEY `subscriptions_id` (`subscriptions_id`),
  ADD KEY `creator_id_refs_user_ptr_id_434b98db` (`creator_id`);

--
-- Indexes for table `users_homepages`
--
ALTER TABLE `users_homepages`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `customuser_id` (`customuser_id`,`page_id`),
  ADD KEY `page_id_refs_id_290bb907` (`page_id`);

--
-- Indexes for table `writetag_log`
--
ALTER TABLE `writetag_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `writetag_log_fbfc09f1` (`user_id`),
  ADD KEY `writetag_log_299e3b72` (`plant_id`),
  ADD KEY `writetag_log_a0221886` (`controller_id`),
  ADD KEY `writetag_log_32d04bc7` (`page_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `alarms`
--
ALTER TABLE `alarms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_message`
--
ALTER TABLE `auth_message`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `controllers`
--
ALTER TABLE `controllers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `countries`
--
ALTER TABLE `countries`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `datalogger_tags`
--
ALTER TABLE `datalogger_tags`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_site`
--
ALTER TABLE `django_site`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `measurements`
--
ALTER TABLE `measurements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `pages`
--
ALTER TABLE `pages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `permissions`
--
ALTER TABLE `permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `plants`
--
ALTER TABLE `plants`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `plants_admins`
--
ALTER TABLE `plants_admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `plants_users`
--
ALTER TABLE `plants_users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `regions`
--
ALTER TABLE `regions`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `relays`
--
ALTER TABLE `relays`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `subscriptions`
--
ALTER TABLE `subscriptions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tags`
--
ALTER TABLE `tags`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `templates`
--
ALTER TABLE `templates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `time_zone`
--
ALTER TABLE `time_zone`
  MODIFY `Time_zone_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `updateperiods`
--
ALTER TABLE `updateperiods`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users_homepages`
--
ALTER TABLE `users_homepages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `writetag_log`
--
ALTER TABLE `writetag_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
