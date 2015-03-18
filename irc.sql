DROP DATABASE IF EXISTS irc;
CREATE DATABASE  irc;
\c irc;
--
-- Table structure for table users
--

DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id serial NOT NULL,
  username varchar(30) NOT NULL default '',
  password varchar(256) NOT NULL default '',
  PRIMARY KEY  (id)
) ;

--
-- Putting data into the users table
--

INSERT INTO users (username, password) VALUES ('kara', 'password');
INSERT INTO users (username, password) VALUES ('bugs', 'bunny');
INSERT INTO users (username, password) VALUES ('dr. who', 'tardis');

--
-- Table structure for table messages
--

DROP TABLE IF EXISTS messages;
CREATE TABLE messages (
  id serial NOT NULL,
  text varchar(256) NOT NULL default '',
  user_id int NOT NULL default '0',
  PRIMARY KEY  (id)
) ;

--
-- Putting data into the messages table
--

INSERT INTO messages (text, user_id) VALUES ('test message', 1);
INSERT INTO messages (text, user_id) VALUES ('chatting is fun!', 1);
INSERT INTO messages (text, user_id) VALUES ('I hear the Ood calling! Time to fly.', 3);
INSERT INTO messages (text, user_id) VALUES ('I love carrots!', 2);
INSERT INTO messages (text, user_id) VALUES ('take a left at albuquerque', 2);




