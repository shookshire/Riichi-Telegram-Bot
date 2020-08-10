import psycopg2
import re

from datetime import datetime

from config import DB_CONFIG
import helper_functions as func

def connect_db():
	return psycopg2.connect(
	  host=DB_CONFIG['db_host'],
	  database=DB_CONFIG['db_database'],
	  user=DB_CONFIG['db_user'],
	  password=DB_CONFIG['db_password']
	)

def get_player_by_name(name):
	conn = connect_db()
	cur = conn.cursor()

	cur.execute("SELECT pid, pname FROM Players where pname=lower('{}')".format(name))
	row = cur.fetchone()

	cur.close()
	conn.close()

	if row is None:
		return None

	return {'id': row[0], 'name': func.handle_name(row[1])}

def get_player_by_id(pid):
	conn = connect_db()
	cur = conn.cursor()

	cur.execute("SELECT pid, pname FROM Players where pid={}".format(pid))
	row = cur.fetchone()

	cur.close()
	conn.close()

	if row is None:
		return None

	return {'id': row[0], 'name': func.handle_name(row[1])}

def set_new_game(game):
	pid = func.get_all_player_id(game['players'])

	sql = "INSERT INTO Game (start_time, initial_value, p1_id, p2_id, p3_id, p4_id, aka, uma_p1, uma_p2, uma_p3, uma_p4, oka) VALUES"
	sql += "(NOW(), {}, {}, {}, {}, {}, '{}', {}, {}, {}, {}, {}) returning gid, to_char(start_time, 'DD-MM-YYYY')".format(game['initial value'], pid[0], pid[1], pid[2], pid[3], game['aka'], game['uma'][0], game['uma'][1], game['uma'][2], game['uma'][3], game['oka'])

	conn = connect_db()
	cur = conn.cursor()

	cur.execute(sql)
	row = cur.fetchone()

	conn.commit()

	cur.close()
	conn.close()

	return row[0], row[1]

def set_new_hand(hand, game_id, player_id):
	conn = connect_db()
	cur = conn.cursor()

	sql = "INSERT INTO Hand (gid, hand_num, wind, round_num, honba, outcome, han, fu, value) VALUES"
	sql += "({}, {}, '{}', {}, {}, '{}', {}, {}, {}) returning hid".format(game_id, hand['hand num'], hand['wind'], hand['round num'], hand['honba'], hand['outcome'], hand['han'], hand['fu'], hand['value'])

	cur.execute(sql)
	hid = cur.fetchone()[0]

	oya = [False]*4
	oya[hand['round num'] - 1] = True
	ioutcome = func.get_individual_outcome(hand)

	for i in range(4):
		sql = "INSERT INTO IndividualHand (gid, hid, initial_pos, pid, position, dealer, outcome, tenpai, riichi, start_score, end_score, score_change, chombo) VALUES"
		sql += "({}, {}, {}, {}, {}, {}, '{}', {}, {}, {}, {}, {}, {})".format(game_id, hid, i+1, player_id[i], hand['position'][i], oya[i], ioutcome[i], hand['tenpai'][i], hand['riichi'][i], hand['initial score'][i], hand['final score'][i], hand['score change'][i], hand['chombo'][i])

		cur.execute(sql)

	conn.commit()
	cur.close()
	conn.close()

	return True

def set_complete_game(game_id, score, position, penalty):
	conn = connect_db()
	cur = conn.cursor()

	sql = "UPDATE Game SET status='complete', p1_score={}, p2_score={}, p3_score={}, p4_score={}, p1_position={}, p2_position={}, p3_position={}, p4_position={}, p1_penalty={}, p2_penalty={}, p3_penalty={}, p4_penalty={} WHERE gid={}".format(score[0], score[1], score[2], score[3], position[0], position[1], position[2], position[3], penalty[0], penalty[1], penalty[2], penalty[3], game_id)

	cur.execute(sql)

	conn.commit()
	cur.close()
	conn.close()

	return True

def delete_last_hand(game_id, hand_num):
	conn = connect_db()
	cur = conn.cursor()

	sql = "DELETE from Hand where gid={} and hand_num={}".format(game_id, hand_num)
	cur.execute(sql)

	conn.commit()
	cur.close()
	conn.close()

	return True

