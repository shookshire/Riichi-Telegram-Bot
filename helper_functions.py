import string
import re


def handle_name(name):
  return string.capwords(name.strip())


def get_player_name(player_info):
  return player_info['name']


def get_max_len(lst):
  return max([len(x) for x in lst])


def map_score_to_string(score):
  score_str = list(map(lambda x: str(x), score))
  length = max(len(ele) for ele in score_str)
  return list(map(lambda x: x.rjust(length), score_str))


##################################################################################
# Printing functions
##################################################################################


def print_select_names(player_names, selected):
  text = ''
  for i in range(len(selected)):
    if selected[i]:
      text += '{}\n'.format(player_names[i])
  return text


def print_select_names_in_order(player_names, riichi_order):
  text = ''
  for i in range(len(riichi_order)):
    idx = riichi_order[i]
    text += '{}. {}\n'.format(i + 1, player_names[idx])
  return text


def print_name_score(player_names, score):
  max_name_len = get_max_len(player_names)
  score_str = map_score_to_string(score)

  text = ''
  for i in range(len(player_names)):
    text += '{}'.format(player_names[i]).ljust(
        max_name_len + 1) + '| {}\n'.format(score_str[i])

  return text


def print_name_score_and_difference(player_names, score, position):
  max_name_len = get_max_len(player_names)
  rounded_position = list(map(lambda x: int(x), position))
  score_str = map_score_to_string(score)

  def get_score_difference(pos):
    if pos == 1:
      return 0
    next_pos = pos - 1
    while not next_pos in rounded_position and next_pos > 1:
      next_pos -= 1
    return score[rounded_position.index(pos)] - score[rounded_position.index(next_pos)]

  def all_players_same_score(pos):
    for p in pos:
      if not p == 2:
        return False
    return True

  score_difference = ['0', '0', '0', '0'] if all_players_same_score(rounded_position) else map_score_to_string(
      list(map(get_score_difference, rounded_position)))

  text = ''
  for i in range(len(player_names)):
    text += '{}'.format(player_names[i]).ljust(
        max_name_len + 1) + '| {} | {}\n'.format(score_str[i], score_difference[i])

  return text


def print_game_confirmation(gid, final_score_text):
  text = '`Hi! A game have been recorded with you as a participant.\n\n`'
  text += '`Game id: {}\n\n`'.format(gid)
  text += final_score_text
  text += '`\n\nIf you did not participate in this game please contact @MrFeng or other SgRiichi admins`'

  return text


def have_3_same_position(position):
  for i in position:
    freq = position.count(i)
    if freq == 3:
      return True, i
  return False, None


def get_uma(uma, position, triple_same_position):
  x = float(position)
  round_down = int(x) - 1
  if triple_same_position:
    return (uma[round_down-1] + uma[round_down] + uma[round_down+1])/3
  if x.is_integer():
    return uma[round_down]
  else:
    return (uma[round_down] + uma[round_down + 1])/2


def print_end_game_result(player_names, score, position, initial_value, uma):
  max_name_len = get_max_len(player_names)
  have_3_same_pos, pos = have_3_same_position(position)

  res = []
  for i in range(4):
    res.append(
        {'name': player_names[i], 'score': score[i], 'position': position[i], 'uma': get_uma(uma, position[i], have_3_same_pos if pos == position[i] else False)})

  res = sorted(res, key=lambda k: k['position'])

  text = 'Name'.ljust(max_name_len + 1) + '| Raw | Pos\n'
  for obj in res:
    text += '{}'.format(obj['name']).ljust(max_name_len + 1) + '|' + '{}'.format(obj['score']).rjust(4) + \
        ' | {}\n'.format(obj['position'])

  text += '\n' + 'Name'.ljust(max_name_len) + '| Net  | Points\n'
  for obj in res:
    net_score = obj['score'] - initial_value
    score_with_uma = net_score + obj['uma'] * 10
    if isinstance(score_with_uma, float) and score_with_uma.is_integer():
      score_with_uma = int(score_with_uma)
    text += '{}'.format(obj['name']).ljust(max_name_len + 1) + \
        '|' + '{}'.format(net_score).rjust(5) + \
        ' |' + '{}'.format(score_with_uma).rjust(5) + '\n'

  return text
