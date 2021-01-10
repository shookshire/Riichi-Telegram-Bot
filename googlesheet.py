import gspread
import string

from datetime import datetime
from config import SPREADSHEET_CONFIG
import helper_functions as func


def connect_spreadsheet():
	gc = gspread.service_account(filename="./service_account.json")
	return gc.open_by_key(SPREADSHEET_CONFIG['sheet_key'])

def get_player_list():
	sh = connect_spreadsheet()
	players = sh.worksheet('players')
	res = players.get_all_records()
	return list(map(lambda x: {'pid': x['pid'], 'name': string.capwords(x['name'].strip()), 'telegram_id': x['telegram_id']}, res))

def get_venue_list():
	sh = connect_spreadsheet()
	venue = sh.worksheet('venue')
	res = venue.get_all_records()
	filtered = list(filter(lambda x: int(x['status']), res))
	return list(map(lambda x: {'vid': x['vid'], 'name': x['name']}, filtered))

def get_mode_list(vid):
	sh = connect_spreadsheet()
	mode = sh.worksheet('mode')
	res = mode.get_all_records()
	filtered = list(filter(lambda x: int(x['status']) and x['vid'] == vid, res))
	return list(map(lambda x: {'mid': x['mid'], 'name': x['name']}, filtered))

def get_last_id(worksheet):
	res = worksheet.col_values(1)
	return int(res[-1]) if len(res) > 1 else 0

def set_game(game, timeout=False):
	gid = set_game_info(game, timeout)
	set_game_result(game, gid)
	set_hand_info(game, gid)
	return gid

def set_game_info(game, timeout=False):
	sh = connect_spreadsheet()
	worksheet = sh.worksheet('game_info')
	last_id= get_last_id(worksheet)
	gid = last_id + 1

	row = [
		gid,
		game['date'],
		game['time'],
		game['initial value'],
		'timeout' if timeout else 'complete',
		game['aka'],
		game['uma'][0],
		game['uma'][1],
		game['uma'][2],
		game['uma'][3],
		game['oka'],
		game['venue']['vid'],
		game['mode']['mid']
	]
	worksheet.append_row(row)
	return gid

def set_game_result(game, gid):
	sh = connect_spreadsheet()
	worksheet = sh.worksheet('game_result')

	for i in range(4):
		row = [
			gid,
			i + 1,
			game['players'][i]['pid'],
			game['final score'][i],
			game['position'][i],
			game['penalty'][i]
		]
		worksheet.append_row(row)

def set_hand_info(game, gid):
	sh = connect_spreadsheet()
	worksheet = sh.worksheet('hand_info')
	hid = get_last_id(worksheet)
	hands = game['hands']

	for i in range(len(hands)):
		hand = hands[i]
		hid += 1
		row = [
			hid,
			gid,
			i+1,
			hand['wind'],
			hand['round num'],
			hand['honba'],
			hand['pool'],
			hand['outcome'],
			hand['han'],
			hand['fu'],
			hand['value']
		]
		worksheet.append_row(row)
		set_hand_result(hand, gid, hid, game['players'])

def set_hand_result(hand, gid, hid, players):
	sh = connect_spreadsheet()
	worksheet = sh.worksheet('hand_result')
	ihid = get_last_id(worksheet)

	oya = [False]*4
	oya[hand['round num'] - 1] = True
	ioutcome = func.get_individual_outcome(hand)

	for i in range(4):
		ihid += 1
		row = [
			ihid,
			gid,
			hid,
			players[i]['pid'],
			hand['position'][i],
			oya[i],
			ioutcome[i],
			hand['tenpai'][i],
			hand['riichi'][i],
			hand['initial score'][i],
			hand['final score'][i],
			hand['score change'][i],
			hand['chombo'][i]
		]
		worksheet.append_row(row)

def set_record_game(game):
	gid = set_record_game_info(game)
	set_record_game_result(game, gid)
	return gid


def set_record_game_info(game):
	sh = connect_spreadsheet()
	worksheet = sh.worksheet('game_info')
	last_id= get_last_id(worksheet)
	gid = last_id + 1

	row = [
		gid,
		datetime.now().strftime("%d-%m-%Y"),
		'',
		game['initial value'],
		'complete',
		game['aka'],
		game['uma'][0],
		game['uma'][1],
		game['uma'][2],
		game['uma'][3],
		game['oka']
	]
	worksheet.append_row(row)
	return gid

def set_record_game_result(game, gid):
	sh = connect_spreadsheet()
	worksheet = sh.worksheet('game_result')

	for i in range(4):
		row = [
			gid,
			i + 1,
			game['players'][i]['pid'],
			game['final score'][i],
			game['position'][i],
			game['penalty'][i]
		]
		worksheet.append_row(row)
