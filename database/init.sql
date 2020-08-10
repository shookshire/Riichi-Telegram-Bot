DROP TABLE IF EXISTS Players CASCADE;
DROP TABLE IF EXISTS Game CASCADE;
DROP TABLE IF EXISTS Hand CASCADE;
DROP TABLE IF EXISTS IndividualHand CASCADE;

CREATE TABLE Players (
	pid SERIAL PRIMARY KEY,
	pname VARCHAR(20) NOT NULL,
	full_name varchar(50),
	ic varchar(20)
);

CREATE OR REPLACE FUNCTION lower_name_of_player()
  RETURNS trigger AS
$$
BEGIN
NEW.pname = LOWER(NEW.pname);
NEW.full_name = LOWER(NEW.full_name);
NEW.ic = UPPER(NEW.ic);
RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

CREATE TRIGGER che_val_befo_ins
  BEFORE INSERT OR UPDATE
  ON Players
  FOR EACH ROW
  EXECUTE PROCEDURE lower_name_of_player();

CREATE TABLE Game (
	gid 				SERIAL PRIMARY KEY,
	start_time 	TIMESTAMP,
	end_time 		TIMESTAMP,
	initial_value	INTEGER,
	status 			VARCHAR(20) NOT NULL default 'in progress',
	p1_id 			INTEGER NOT NULL,
	p2_id 			INTEGER NOT NULL,
	p3_id 			INTEGER NOT NULL,
	p4_id 			INTEGER NOT NULL,
	aka					VARCHAR(20),
	uma_p1			INTEGER DEFAULT 0,
	uma_p2			INTEGER DEFAULT 0,
	uma_p3			INTEGER DEFAULT 0,
	uma_p4			INTEGER DEFAULT 0,
	oka					INTEGER DEFAULT 0,
	p1_score		INTEGER,
	p2_score		INTEGER,
	p3_score		INTEGER,
	p4_score		INTEGER,
	p1_position	DECIMAL(2,1),
	p2_position	DECIMAL(2,1),
	p3_position	DECIMAL(2,1),
	p4_position	DECIMAL(2,1),
	p1_penalty	INTEGER,
	p2_penalty	INTEGER,
	p3_penalty	INTEGER,
	p4_penalty	INTEGER,
	FOREIGN KEY (p1_id) REFERENCES Players,
	FOREIGN KEY (p2_id) REFERENCES Players,
	FOREIGN KEY (p3_id) REFERENCES Players,
	FOREIGN KEY (p4_id) REFERENCES Players
);

CREATE TABLE Hand (
	hid				serial primary key,
	gid				INTEGER not null,
	hand_num	INTEGER not null,
	wind			VARCHAR(1) NOT NULL,
	round_num	INTEGER NOT NULL,
	honba			INTEGER	NOT NULL DEFAULT 0,
	outcome		VARCHAR(10) NOT NULL,
	han 			INTEGER,
	fu				INTEGER,
	value			INTEGER,
	FOREIGN key (gid) references Game,
	UNIQUE (gid, hand_num),
	CHECK (wind = 'E' OR wind = 'S' OR wind = 'W')
);

CREATE TABLE IndividualHand (
	ihid serial primary key,
	gid	INTEGER NOT NULL,
	hid	INTEGER NOT NULL,
	initial_pos	INTEGER NOT NULL,
	pid INTEGER NOT NULL,
	position DECIMAL(2,1) NOT NULL,
	dealer boolean NOT NULL,
	outcome varchar(20) not null,
	tenpai boolean,
	riichi boolean not null default false,
	start_score integer not null,
	end_score integer not null,
	score_change integer not null default 0,
	chombo boolean default False,
	FOREIGN key (gid) references Game(gid) on delete cascade,
	FOREIGN key (hid) references Hand(hid) on delete cascade,
	FOREIGN key (pid) references Players(pid) on delete cascade
);

insert into Players (pname) values ('Nlyzmq');
insert into Players (pname) values ('Zmmx');
insert into Players (pname) values ('Jzd');
insert into Players (pname) values ('Bababa');
insert into Players (pname) values ('Fits');
insert into Players (pname) values ('Rub');
insert into Players (pname) values ('Burn');
insert into Players (pname) values ('Under World');
insert into Players (pname) values ('Aspergers');
insert into Players (pname) values ('Luck Sack');
insert into Players (pname) values ('Suay Sack');