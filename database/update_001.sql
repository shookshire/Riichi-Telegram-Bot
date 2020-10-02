CREATE TABLE Venue (
	vid VARCHAR(3) PRIMARY KEY,
	vname varchar(20),
	description varchar(100),
	status varchar(20) default 'open'
);

CREATE TABLE Mode (
	mid SERIAL PRIMARY KEY,
	vid VARCHAR(3),
	mname varchar(50),
	description varchar(100),
	start_time 	TIMESTAMP default '0001-01-01',
	end_time 		TIMESTAMP default '9999-01-01',
	FOREIGN KEY (vid) REFERENCES Venue ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE Game
ADD COLUMN vid VARCHAR(3),
ADD COLUMN mid INTEGER,
ADD CONSTRAINT game_venue_fk FOREIGN KEY (vid) REFERENCES Venue (vid),
ADD CONSTRAINT game_mode_fk FOREIGN KEY (mid) REFERENCES Mode (mid);
