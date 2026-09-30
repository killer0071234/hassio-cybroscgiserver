INSERT INTO `auth_user` (`id`, `username`, `first_name`, `last_name`, `email`, `password`, `is_staff`, `is_active`, `is_superuser`, `last_login`, `date_joined`) VALUES
(1, 'admin', '', '', 'your.email@email.email', 'sha1$3c6bb$5844790e65fe8350d8906710030d600dd771310a', 1, 1, 1, '2014-10-18 09:10:34', '2011-09-09 12:28:18');

INSERT INTO `permissions` (`id`, `is_server_admin`, `can_manage_plants`, `can_manage_users`, `can_manage_templates`, `can_manage_controllers`, `can_manage_media`, `can_manage_site_content`, `rw_tags_access`) VALUES
(1, 1, 1, 1, 1, 1, 1, 1, 1);

INSERT INTO `subscriptions` (`id`, `alarms_events_subscription`) VALUES
(1, 0);

INSERT INTO `users` (`user_ptr_id`, `name`, `login_count`, `permissions_id`, `creator_id`, `last_ip`, `subscriptions_id`) VALUES
(1, 'Administrator', 0, 1, NULL, '', 1);

INSERT INTO `updateperiods` (`id`, `text`, `period`) VALUES
(1, '2 s', 2),
(2, '10 s', 10),
(3, '30 s', 30),
(4, '1 min', 60),
(5, '10 min', 600),
(6, '1s', 1),
(7, 'Never', 9999);

INSERT INTO `pages` (`id`, `name`, `description`, `parent_id`, `plant_id`, `path`, `data_folder`, `content`, `author_id`, `modified_by_id`, `order`, `update_period_id`, `public`, `published`, `date_added`, `last_modified`) VALUES
(
 1,
 'Home',
 'This is a home page',
 NULL,
 NULL,
 'home',
 './',
 'Home',
 1,
 1,
 0,
 7,
 0,
 1,
 '2010-05-18 10:44:58',
 '2024-12-02 10:53:21'
),
(
 502,
 'Server status',
 'Real-time server status, statistics and performance data',
 1,
 NULL,
 '',
 '',
 '<img src=\"/data/media/site-content/server.png\" align=\"right\" style=\"margin-top:-80px; margin-right:25px;\" />\n\n<table border=\"0\" cellspacing=\"0\" cellpadding=\"2\" width=\"50%\">\n<tbody>\n\n<tr>\n<td width=\"50%\">Server version</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.server_version</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Server uptime</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.server_uptime</var>\n</cybro>\n</td>\n</tr>\n\n</tbody>\n</table>\n<br />\n\n<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->\n\n<h3>Push server</h3>\n\n<table border=\"0\" cellspacing=\"0\" cellpadding=\"2\" width=\"50%\">\n<tbody>\n\n<tr>\n<td width=\"50%\">Server status (port 8442)</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.push_port_status</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Received push messages</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.push_count</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Acknowledge errors</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.push_ack_errors</var>\n</cybro>\n</td>\n</tr>\n\n</tbody>\n</table>\n<br />\n\n<div class=\"child_list\">\n<div class=\"item\">\n<pre style=\"font-size: 8.3pt;\">\n<cybro>\n  <type>decimal</type>\n  <var>sys.push_list</var>\n</cybro>\n</pre>\n</div>\n</div>\n<br />\n\n<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->\n\n<h3>SCGI server</h3>\n\n<table border=\"0\" cellspacing=\"0\" cellpadding=\"2\" width=\"50%\">\n<tbody>\n\n<tr>\n<td width=\"50%\">Server status (port 4000)</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.scgi_port_status</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Total requests</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.scgi_request_count</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Pending requests</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.scgi_request_pending</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Cache request time</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.cache_request</var>\n</cybro> sec\n</td>\n</tr>\n\n<tr>\n<td>Cache valid time</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.cache_valid</var>\n</cybro> sec\n</td>\n</tr>\n\n<tr>\n<td>Received UDP messages</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.udp_rx_count</var>\n</cybro>\n</td>\n</tr>\n\n<tr>\n<td>Transmitted UDP messages</td>\n<td>\n<cybro>\n  <type>decimal</type>\n  <var>sys.udp_tx_count</var>\n</cybro>\n</td>\n</tr>\n\n</tbody>\n</table>',
 1,
 1,
 2,
 1,
 0,
 1,
 '2013-01-25 22:29:10',
 '2024-11-12 11:32:17'
);