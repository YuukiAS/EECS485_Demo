PRAGMA foreign_keys = ON; -- turn on foreign key support

CREATE TABLE users(
  username VARCHAR(20) NOT NULL, -- if we use CHARACTER, the length will be constant
  fullname VARCHAR(40) NOT NULL,
  email VARCHAR(40) NOT NULL,
  "filename" VARCHAR(64) NOT NULL, -- escape
  "password" VARCHAR(256) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP, -- * current time
  PRIMARY KEY(username)
);

CREATE TABLE posts( 
  postid INTEGER PRIMARY KEY AUTOINCREMENT,  -- * like 1, 2, 3, ...
  "filename" VARCHAR(64) NOT NULL, 
  "owner" VARCHAR(20) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY("owner") REFERENCES users(username) ON DELETE CASCADE -- * row will be automatically deleted
);

CREATE TABLE "following"( 
    username1 VARCHAR(20) NOT NULL, -- def username1 follows username2
    username2 VARCHAR(20) NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,    
    PRIMARY KEY(username1, username2),
    FOREIGN KEY(username1) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY(username2) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE comments(
  commentid INTEGER PRIMARY KEY AUTOINCREMENT,
  "owner" VARCHAR(20) NOT NULL,
  postid INTEGER NOT NULL,
  "text" VARCHAR(1024) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY("owner") REFERENCES users(username) ON DELETE CASCADE,
  FOREIGN KEY(postid) REFERENCES posts(postid) ON DELETE CASCADE
);

CREATE TABLE likes(
  likeid INTEGER PRIMARY KEY AUTOINCREMENT,
  "owner" VARCHAR(20) NOT NULL,
  postid INTEGER NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY("owner") REFERENCES users(username) ON DELETE CASCADE,
  FOREIGN KEY(postid) REFERENCES posts(postid) ON DELETE CASCADE
);
