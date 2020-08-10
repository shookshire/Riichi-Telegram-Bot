import string
import re
from constants import *

def handle_name(name):
	return string.capwords(name.strip())

def get_player_id(player_info):
	return player_info['id']

def get_player_name(player_info):
	return player_info['name']

def get_all_player_id(players):
	player_ids = [get_player_id(p) for p in players]
	return player_ids

def get_all_player_name(players):
	player_names = [get_player_name(p) for p in players]
	return player_names

def is_valid_player_name(text, player_names):
  name = handle_name(text)
  return name in player_names

def get_player_idx(text, player_names):
  name = handle_name(text)
  return player_names.index(name)

def get_last_valid_hand(hands):
	for i in range(len(hands)):
		hand = hands[-i]
		if not hand['outcome'] == 'Chombo':
			return hand

	return None

def is_renchan(hand):
	if (hand['outcome'] == 'Tsumo' or hand['outcome'] == 'Ron') and (hand['winner idx'] + 1 == hand['round num']):
		return True

	if hand['outcome'] == 'Draw' and hand['tenpai'][hand['round num'] - 1]:
		return True

	return False

def get_next_wind_round(wind, round_num):
	if round_num < 4:
		return wind, round_num + 1

	if wind == 'E':
		return 'S', 1

	return 'W', 1

def process_hand(hand):
	score_change, pool = get_total_score_change(hand)
	hand['score change'] = score_change
	hand['pool'] = pool
	hand['final score'] = get_new_score(hand['initial score'], score_change)
	hand['position'] = get_position(hand['final score'])

	if hand['outcome'] == 'Tsumo' or hand['outcome'] == 'Ron':
		hand['value'] = score_change[hand['winner idx']]

def process_game(game):
	game['final score'] = game['hands'][-1]['final score'] if len(game['hands']) else [250, 250, 250, 250]
	game['position'] = game['hands'][-1]['position'] if len(game['hands']) else [2.5,2.5,2.5,2.5]


def get_position(score):
	position = [0.5, 0.5, 0.5, 0.5]
	for i in range(4):
		s = score[i]
		for x in score:
			if x == s:
				position[i] += 0.5
			if x > s:
				position[i] += 1
	return position

def get_next_hand_wind_round_honba(prev_hand):
	wind = prev_hand['wind']
	round_num = prev_hand['round num']
	honba = prev_hand['honba']

	if is_renchan(prev_hand):
		honba += 1
	else:
		wind, round_num = get_next_wind_round(wind, round_num)
		if prev_hand['outcome'] == 'Draw':
			honba += 1
		else:
			honba = 0

	return wind, round_num, honba

def create_new_hand(hands):
	prev_hand = get_last_valid_hand(hands)

	new_hand = {
		'hand num': 1 if len(hands) == 0 else hands[-1]['hand num'] + 1,
		'wind': 'E',
		'round num': 1,
		'honba': 0,
		'outcome': '',
		'han': 0,
		'fu': 0,
		'value': 0,
		'winner idx': '',
		'loser idx': '',
		'tenpai': [False, False, False, False],
		'riichi': [False, False, False, False],
		'initial score': [250, 250, 250, 250],
		'final score': [250, 250, 250, 250],
		'position': [2.5,2.5,2.5,2.5],
		'chombo': [False, False, False, False],
		'score change': [0,0,0,0],
		'pool': 0,
		'penalty': [0,0,0,0]
	}

	if prev_hand is None:
		return new_hand

	wind, round_num, honba = get_next_hand_wind_round_honba(prev_hand)

	new_hand['wind'] = wind
	new_hand['round num'] = round_num
	new_hand['honba'] = honba
	new_hand['initial score'] = prev_hand['final score']
	new_hand['final score'] = prev_hand['final score']
	new_hand['pool'] = prev_hand['pool']

	return new_hand

def get_valid_fu(outcome, han):
  lst = []
  if outcome == 'Tsumo':
      lst = [*TSUMO_VALUE[han]]
  else:
      lst = [*RON_VALUE[han]]
  lst.sort()
  return lst

def is_oya_win(hand):
	if hand['winner idx'] + 1 == hand['round num']:
		return True
	return False

def get_new_score(prev_score, score_change):
  return [x + y for x, y in zip(score_change, prev_score)]

def get_total_score_change(hand):
  score_change = get_tsumo_score_change(hand, hand['honba']) if hand['outcome'] == 'Tsumo' else get_ron_score_change(hand, hand['honba']) if hand['outcome'] == 'Ron' else get_draw_score_change(hand)
  stick_score_change, new_pool = get_riichi_stick_change(hand, hand['pool'])

  return [x + y for x, y in zip(score_change, stick_score_change)], new_pool

def get_tsumo_score_change(hand, honba):
  winner = hand['winner idx']
  score_change = [0,0,0,0]

  if is_oya_win(hand):
    value = TSUMO_OYA_VALUE[hand['han']][hand['fu']] if re.match('^[1-4]$', hand['han']) else TSUMO_OYA_VALUE[hand['han']]
    for i in range(4):
      if not i == winner:
        score_change[i] = -value - honba
    score_change[winner] = -sum(score_change)
  else:
    oya_value = TSUMO_OYA_VALUE[hand['han']][hand['fu']] if re.match('^[1-4]$', hand['han']) else TSUMO_OYA_VALUE[hand['han']]
    value = TSUMO_VALUE[hand['han']][hand['fu']] if re.match('^[1-4]$', hand['han']) else TSUMO_VALUE[hand['han']]
    for i in range(4):
      if not i == winner:
        score_change[i] = -value - honba
    score_change[hand['round num'] - 1] = -oya_value - honba
    score_change[winner] = -sum(score_change)

  return score_change

def get_ron_score_change(hand, honba): 
  winner = hand['winner idx']
  loser = hand['loser idx']
  score_change = [0,0,0,0]

  if is_oya_win(hand):
    value = RON_OYA_VALUE[hand['han']][hand['fu']] if re.match('^[1-4]$', hand['han']) else RON_OYA_VALUE[hand['han']]
  else:
    value = RON_VALUE[hand['han']][hand['fu']] if re.match('^[1-4]$', hand['han']) else RON_VALUE[hand['han']]

  score_change[winner] = value + honba*3
  score_change[loser] = -value - honba*3
  return score_change

def get_draw_score_change(hand):
  tenpai = hand['tenpai']
  score_change = [0,0,0,0]

  num_tenpai = 0
  for t in tenpai:
    if t:
      num_tenpai += 1

  pos_value = 0
  neg_value = 0
  if num_tenpai == 1:
  	pos_value = 30
  	neg_value = 10
  if num_tenpai == 2:
  	pos_value = 15
  	neg_value = 15
  if num_tenpai == 3:
  	pos_value = 10
  	neg_value = 30

  for i in range(len(tenpai)):
  	if tenpai[i]:
  		score_change[i] = pos_value
  	else:
  		score_change[i] = neg_value

  return score_change

def get_riichi_stick_change(hand, pool):
	riichi = hand['riichi']
	score_change = [0,0,0,0]
	for i in range(len(riichi)):
		if riichi[i]:
			pool += 10
			score_change[i] = -10

	if hand['outcome'] == 'Tsumo' or hand['outcome'] == 'Ron':
		winner = hand['winner idx']
		score_change[winner] += pool
		pool = 0

	return score_change, pool
  
def get_individual_outcome(hand):
	if hand['outcome'] == 'Draw':
		return ['Draw']*4
	if hand['outcome'] == 'Chombo':
		return ['Chombo']*4
	if hand['outcome'] == 'Tsumo':
		outcome = ['Tsumo-loss']*4
		outcome[hand['winner idx']] = 'Tsumo'
		return outcome
	if hand['outcome'] == 'Ron':
		outcome = ['']*4
		outcome[hand['winner idx']] = 'Ron'
		outcome[hand['loser idx']] = 'Deal-in'
		return outcome 

def get_max_len(lst):
	return max([len(x) for x in lst])

##################################################################################
# Printing functions
##################################################################################

def print_game_settings_without_id(game):
	uma = game['uma']
	players = game['players']
	player_names = [get_player_name(p) for p in players]

	text = '`Game Settings\n---------------------------------------\n'
	text += 'Aka | {}\n'.format(game['aka'])
	text += 'Uma | {}, {}, {}, {}\n'.format(uma[0], uma[1], uma[2], uma[3])
	text += 'Oka | {}\n'.format(game['oka'])

	text += '\n\nPlayer Names:\n'
	text += '{}\n{}\n{}\n{}`'.format(player_names[0], player_names[1], player_names[2], player_names[3])

	return text

def print_game_settings_info(game):
	text = '`Id: {}\n`'.format(game['id'])
	text += '`Date: {}\n`'.format(game['date'])
	text += print_game_settings_without_id(game)

	return text

def print_select_names(player_names, selected):
	text = ''
	for i in range(len(selected)):
		if selected[i]:
			text += '`{}\n`'.format(player_names[i])
	return text

def print_name_score(player_names, score):
	max_name_len = get_max_len(player_names)
	
	text = '`'
	for i in range(len(player_names)):
		text += '{}'.format(player_names[i]).ljust(max_name_len + 1) + '| {}\n'.format(score[i])
	text += '`'

	return text

def print_hand_settings(hand, player_names):
	text = '`Hand Number: {}\n`'.format(hand['hand num'])
	text += '`Round: {}{}  {} Honba\n\n`'.format(hand['wind'], hand['round num'], hand['honba'])
	
	if any(hand['chombo']):
		text += '`Who Chombo:\n`'
		text += print_select_names(player_names, hand['chombo'])
		return text

	text += '`Outcome: {}\n\n`'.format(hand['outcome'])
	if hand['outcome'] == 'Draw':
		text += '`Who Tenpai:\n`'
		text += print_select_names(player_names, hand['tenpai'])
		text += '`\n`'
	else:
		if hand['outcome'] == 'Tsumo':
			text += '`{} Tsumo\n`'.format(player_names[hand['winner idx']])
		else:
			text += '`{} Ron {}\n`'.format(player_names[hand['winner idx']], player_names[hand['loser idx']])
		text += '`{} Han`'.format(hand['han'])
		if hand['fu']:
			text += '` {}`'.format(hand['fu'])
			if not hand['fu'] == 'mangan':
				text += '` Fu`'
		text += '`\n\n`'

	text += '`Who Riichi:\n`'
	text += print_select_names(player_names, hand['riichi'])
	return text

def print_score_change(hand, player_names):
	text = '`Score Change:\n---------------------------------------\n`'
	text += print_name_score(player_names, hand['score change'])
	text += '`\nCurrent Score:\n---------------------------------------\n`'
	text += print_name_score(player_names, hand['final score'])
	text += '`\nValue in pool: {}`'.format(hand['pool'])

	return text

def print_penalty(penalty, player_names):
	text = '`Penalty:\n---------------------------------------\n`'
	text += print_name_score(player_names, penalty)

	return text


def print_current_game_state(hands, player_names):
	if len(hands) == 0:
		score = [250, 250, 250, 250]
		pool = 0
		wind = 'E'
		rnd = 1
		honba = 0
	else:
		hand = hands[-1]
		score = hand['final score']
		pool = hand['pool']
		wind, rnd, honba = get_next_hand_wind_round_honba(hand)

	text = '`\nCurrent Score:\n---------------------------------------\n`'
	text += print_name_score(player_names, score)
	text += '`\nValue in pool: {}\n\n`'.format(pool)
	text += '`Next Hand:\n{}{}  {} Honba`'.format(wind, rnd, honba)

	return text