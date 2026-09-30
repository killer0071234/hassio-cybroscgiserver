
ALTER TABLE alarms CHANGE COLUMN timestamp_ack timestamp_ack datetime NOT NULL; # was datetime DEFAULT '0000-00-00 00:00:00'
ALTER TABLE alarms CHANGE COLUMN timestamp_gone timestamp_gone datetime NOT NULL; # was datetime DEFAULT '0000-00-00 00:00:00'
ALTER TABLE alarms CHANGE COLUMN type type int(11) NOT NULL; # was smallint(6) NOT NULL
ALTER TABLE alarms CHANGE COLUMN timestamp_raise timestamp_raise datetime NOT NULL; # was datetime NOT NULL DEFAULT '0000-00-00 00:00:00'
ALTER TABLE controllers CHANGE COLUMN created_id created_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE controllers CHANGE COLUMN owner_id owner_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE controllers ADD INDEX plant_id_refs_id_9918366d (plant_id);
ALTER TABLE controllers ADD INDEX owner_id_refs_user_ptr_id_7e341e7c (owner_id);
ALTER TABLE controllers ADD INDEX created_id_refs_user_ptr_id_7e341e7c (created_id);
ALTER TABLE measurements CHANGE COLUMN timestamp timestamp datetime NOT NULL; # was datetime NOT NULL DEFAULT '0000-00-00 00:00:00'
ALTER TABLE pages CHANGE COLUMN author_id author_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE pages CHANGE COLUMN modified_by_id modified_by_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE pages CHANGE COLUMN update_period_id update_period_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE pages ADD INDEX plant_id_refs_id_8cb21e6e (plant_id);
ALTER TABLE pages ADD INDEX update_period_id_refs_id_9ad09da0 (update_period_id);
ALTER TABLE pages ADD INDEX parent_id_refs_id_3067db9b (parent_id);
ALTER TABLE pages ADD INDEX author_id_refs_user_ptr_id_d65b5c83 (author_id);
ALTER TABLE plants CHANGE COLUMN author_id author_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE plants CHANGE COLUMN homepage_id homepage_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE plants CHANGE COLUMN modified_by_id modified_by_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE plants ADD INDEX author_id_refs_user_ptr_id_36590f74 (author_id);
ALTER TABLE plants ADD INDEX homepage_id_refs_id_fa444fa4 (homepage_id);
ALTER TABLE relays CHANGE COLUMN session_id session_id int(11) NOT NULL; # was int(11) unsigned NOT NULL
ALTER TABLE relays CHANGE COLUMN last_message last_message datetime NOT NULL; # was datetime DEFAULT NULL
ALTER TABLE relays DROP INDEX relays_user_id; # was INDEX (user_id)
ALTER TABLE relays ADD INDEX user_id_refs_user_ptr_id_2c1e7d40 (user_id);
ALTER TABLE templates CHANGE COLUMN author_id author_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE templates CHANGE COLUMN modified_by_id modified_by_id int(11) DEFAULT NULL; # was int(11) NOT NULL
ALTER TABLE templates ADD INDEX author_id_refs_user_ptr_id_1f1807ac (author_id);
ALTER TABLE users ADD INDEX creator_id_refs_user_ptr_id_434b98db (creator_id);

CREATE TABLE IF NOT EXISTS subscriptions (
  id int(11) NOT NULL AUTO_INCREMENT,
  alarms_events_subscription tinyint(1) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS reports (
  id int(11) NOT NULL AUTO_INCREMENT,
  plant_id int(11) NOT NULL,
  timestamp datetime NOT NULL,
  type int(11) NOT NULL,
  timestamp_sent datetime,
  report_text text,
  report_html text,
  PRIMARY KEY (id),
  KEY reports_plant_id (plant_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

ALTER TABLE plants ADD timezone VARCHAR(64) NOT NULL;

ALTER TABLE users ADD subscriptions_id int(11) NOT NULL;

UPDATE plants
  SET timezone = 'UTC';

delimiter //
DROP PROCEDURE IF EXISTS user_subscr_update //
CREATE PROCEDURE user_subscr_update()
BEGIN
  DECLARE done INT DEFAULT FALSE;
  DECLARE usr_id, usr_sub INT;
  DECLARE sub_cnt INT;
  DECLARE usr_upd CURSOR FOR SELECT user_ptr_id, subscriptions_id FROM users;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

  OPEN usr_upd;

  upd_loop: LOOP
    FETCH usr_upd INTO usr_id, usr_sub;
    IF done THEN
      LEAVE upd_loop;
    END IF;
    SELECT COUNT(*) INTO sub_cnt FROM subscriptions WHERE id = usr_sub;
    IF sub_cnt = 0 THEN
      INSERT INTO subscriptions(alarms_events_subscription) VALUES (0);
      SET usr_sub = last_insert_id();
      UPDATE users SET subscriptions_id = usr_sub WHERE user_ptr_id = usr_id;
    END IF;
  END LOOP;

  CLOSE usr_upd;
END//
CALL user_subscr_update() //
DROP PROCEDURE IF EXISTS user_subscr_update //
delimiter ;

ALTER TABLE users ADD UNIQUE KEY subscriptions_id(subscriptions_id);

ALTER TABLE auth_user MODIFY COLUMN email VARCHAR(255);

ALTER TABLE relays CHANGE COLUMN session_id session_id int(11) unsigned NOT NULL;
ALTER TABLE relays MODIFY COLUMN last_message DATETIME DEFAULT NULL;