PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
CREATE TABLE users(
    key USER_KEY PRIMARY KEY,
    ident TEXT UNIQUE NOT NULL,
    permissions INT);
INSERT INTO users VALUES(X'23facc4a03aee5478872172db316e564','kreuz',2);
INSERT INTO users VALUES(X'384e240b7cd76743ac7b8d4a253800d0','stern',2);
CREATE TABLE groupings(
    key GROUPING_KEY PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    host_key USER_KEY NOT NULL,
    begin_date DATETIME NOT NULL,
    final_date DATETIME NOT NULL,
    close_date DATETIME,
    policy TEXT NOT NULL,
    max_group_size INT NOT NULL,
    member_reserve INT NOT NULL,
    note TEXT NOT NULL,
    FOREIGN KEY(host_key) REFERENCES users(key));
INSERT INTO groupings VALUES(X'5c55a3043105724bbfcbe386cee31b97','QNW454','PM',X'23facc4a03aee5478872172db316e564','20190205-133700.000000','20190206-133700.000000',NULL,'RD',6,6,'Einführung in das Projektmanagement: Agiles Studieren');
CREATE TABLE registrations(
    grouping_key GROUPING_KEY NOT NULL,
    user_key USER_KEY NOT NULL,
    preferences TEXT NOT NULL,
    PRIMARY KEY(grouping_key, user_key),
    FOREIGN KEY(grouping_key) REFERENCES groupings(key),
    FOREIGN KEY(user_key) REFERENCES users(key));
CREATE TABLE groups(
    grouping_key GROUPING_KEY NOT NULL,
    group_no INT NOT NULL,
    user_key USER_KEY NOT NULL,
    FOREIGN KEY(grouping_key) REFERENCES groupings(key),
    FOREIGN KEY(user_key) REFERENCES users(key));
CREATE INDEX idx_groups ON groups(grouping_key)
;
COMMIT;
