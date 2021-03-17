import string
import re


def handle_name(name):
  return string.capwords(name.strip())


def get_player_name(player_info):
  return player_info['name']


def get_max_len(lst):
  return max([len(x) for x in lst])

##################################################################################
# Printing functions
##################################################################################


def print_select_names(player_names, selected):
  text = ''
  for i in range(len(selected)):
    if selected[i]:
      text += '{}\n'.format(player_names[i])
  return text


def print_name_score(player_names, score):
  max_name_len = get_max_len(player_names)

  text = ''
  for i in range(len(player_names)):
    text += '{}'.format(player_names[i]).ljust(
        max_name_len + 1) + '| {}\n'.format(score[i])

  return text


def print_game_confirmation(gid, final_score_text):
  text = '`Hi! A game have been recorded with you as a participant.\n\n`'
  text += '`Game id: {}\n\n`'.format(gid)
  text += final_score_text
  text += '`\n\nIf you did not participate in this game please contact @MrFeng or other SgRiichi admins`'

  return text


def print_end_game_result(player_names, score, position, initial_value):

  max_name_len = get_max_len(player_names)
  res = []
  for i in range(4):
    res.append(
        {'name': player_names[i], 'score': score[i], 'position': position[i]})

  res = sorted(res, key=lambda k: k['position'])

  text = ''
  for obj in res:
    text += '{}'.format(obj['name']).ljust(max_name_len) + '|{}'.format(obj['score']) + \
        '|{}'.format(obj['position']) + \
        '|{}\n'.format(obj['score'] - initial_value)

  return text
