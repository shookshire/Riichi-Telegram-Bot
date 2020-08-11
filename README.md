# Riichi Telegram Bot

## Implemented Features

#### Version 1.1

```
1. Added sending private messge to SMCRM users upon game completion
```

#### Version 1.0

```
1. Complete Riichi score tracker
2. Deleting of last recorded hand as a means of correcting mistakes
3. Connect to and store game information to SMCRM db
4. Allow for non SMCRM members to use the app without game storing functionalities
```

## Setup

#### 1. Initialize Database

###### Create a database named riichi and run the following command

```sh
cd ${repo_dir_location}/database/
psql riichi <your_db_username>
\i init.sql
```

###### This will setup the database tables

---

#### 2. Update config file

###### Open config.py loacted in ${repo_dir_location} and edit the dictionaries accordingly

```
bot_token: Token for the telegram bot obtained form bot father
db_host: Host of the db eg. localhost
db_database: Name of the database eg. riichi
db_user: <your_db_username>
db_password: <your_db_password>
```

---

#### 3. Run the system

```sh
cd ${repo_dir_location}/
python app.py
```
