from constants import SEAT_NAME, MCR_SEAT_ORDER
import copy


def generate_new_hand(hands, player_list=[]):
  if len(hands) == 0:
    new_hand = {
        'wind': 0,
        'round': 1,
        'initial score': [
            {'name': player_list[0]['name'], 'score': 0},
            {'name': player_list[1]['name'], 'score': 0},
            {'name': player_list[2]['name'], 'score': 0},
            {'name': player_list[3]['name'], 'score': 0},
        ],
        'final score': [
            {'name': player_list[0]['name'], 'score': 0},
            {'name': player_list[1]['name'], 'score': 0},
            {'name': player_list[2]['name'], 'score': 0},
            {'name': player_list[3]['name'], 'score': 0},
        ]
    }

    hands.append(new_hand)
    return

  prev_hand = hands[-1]

  wind = prev_hand['wind']
  round_num = prev_hand['round'] + 1
  score = prev_hand['final score'][:]

  if round_num > 4:
    wind += 1
    round_num = 1
    score = [score[i] for i in MCR_SEAT_ORDER[wind]]

  new_hand = {
      'wind': wind,
      'round': round_num,
      'initial score': copy.deepcopy(score),
      'final score':  copy.deepcopy(score)
  }

  hands.append(new_hand)


def process_hand(hand, value):
  score = hand['final score']
  winner = hand['winner']
  outcome = hand['outcome']

  if outcome == 'Tsumo':
    for p in score:
      if p['name'] == winner:
        p['score'] += (value + 8) * 3
      else:
        p['score'] -= value + 8

  if outcome == 'Ron':
    loser = hand['loser']
    for p in score:
      if p['name'] == winner:
        p['score'] += value + 8*3
      elif p['name'] == loser:
        p['score'] -= value + 8
      else:
        p['score'] -= 8


def have_next_hand(hands):
  last_hand = hands[-1]
  if last_hand['wind'] == 3 and last_hand['round'] == 4:
    return False

  return True


def get_max_len(lst):
  return max([len(x['name']) for x in lst])


def print_score(score):
  max_name_len = get_max_len(score)

  text = '`'
  for i in range(len(score)):
    text += '{}'.format(score[i]['name']).ljust(max_name_len +
                                                1) + '| {}\n'.format(score[i]['score'])
  text += '`'

  return text


def print_current_game_state(hands):
  hand = hands[-1]

  text = '`Current situation: {} {}\n\n`'.format(
      SEAT_NAME[hand['wind']], hand['round'])
  text += print_score(hand['initial score'])
  return text
