import re
from helper_functions import print_name_score, print_select_names, get_max_len, print_select_names_in_order
from constants import TSUMO_VALUE, RON_VALUE, TSUMO_OYA_VALUE, TSUMO_OYA_KIRIAGE_VALUE, TSUMO_KIRIAGE_VALUE, RON_OYA_VALUE, RON_OYA_KIRIAGE_VALUE, RON_KIRIAGE_VALUE


class Hand:
  def __init__(self, players, kiriage, chombo_option, chombo_value, hand=None, initial_value=250):
    self.outcome = None
    self.han = []
    self.fu = []
    self.value = 0
    self.winners = []
    self.loser = None
    self.tenpai = [False, False, False, False]
    self.riichi = [False, False, False, False]
    self.riichi_order = []
    self.final_score = None
    self.position = None
    self.chombo = [False, False, False, False]
    self.score_change = []
    self.value = []

    self.players = players
    self.kiriage = kiriage
    self.chombo_option = chombo_option
    self.chombo_value = chombo_value
    if hand is None:
      self.hand_num = 1
      self.wind = 'E'
      self.round_num = 1
      self.honba = 0
      self.initial_score = [initial_value]*4
      self.pool = 0
    else:
      self.hand_num = hand.hand_num + 1
      self.wind, self.round_num, self.honba = hand.get_next_wind_round_honba()
      self.initial_score = hand.final_score
      self.pool = hand.pool

  def rechan(self):
    if self.outcome in ['Tsumo', 'Ron'] and self.round_num - 1 in self.winners:
      return True
    if self.outcome in ['Draw', 'Nagashi Mangan'] and self.tenpai[self.round_num - 1]:
      return True
    return False

  def get_next_wind_round(self):
    if self.round_num < 4:
      return self.wind, self.round_num + 1
    if self.wind == 'E':
      return 'S', 1
    if self.wind == 'S':
      return 'W', 1
    return 'N', 1

  def get_next_wind_round_honba(self):
    if self.outcome == 'Chombo':
      return self.wind, self.round_num, self.honba
    if self.outcome == 'Mid Game Draw':
      return self.wind, self.round_num, self.honba+1
    wind = self.wind
    round_num = self.round_num
    honba = self.honba
    if self.rechan():
      honba += 1
    else:
      wind, round_num = self.get_next_wind_round()
      if self.outcome in ['Draw', 'Nagashi Mangan']:
        honba += 1
      else:
        honba = 0
    return wind, round_num, honba

  def toggle_riichi(self, name):
    idx = self.players.get_player_id(name)
    if idx is None:
      return False, 'invalid'
    self.riichi[idx] = not self.riichi[idx]
    if idx in self.riichi_order:
      self.riichi_order.remove(idx)
    self.riichi_order.append(idx)
    return True, None

  def toggle_tenpai(self, name):
    idx = self.players.get_player_id(name)
    if idx is None:
      return False, 'invalid'
    self.tenpai[idx] = not self.tenpai[idx]
    return True, None

  def toggle_chombo(self, name):
    idx = self.players.get_player_id(name)
    if idx is None:
      return False, 'invalid'
    self.chombo[idx] = not self.chombo[idx]
    return True, None

  def set_winner(self, name):
    idx = self.players.get_player_id(name)
    if idx is None:
      return False, 'invalid'
    if idx in self.winners or idx == self.loser:
      return False, 'duplicate'
    self.winners.append(idx)
    self.han.append('0')
    self.fu.append('0')
    return True, None

  def set_loser(self, name):
    idx = self.players.get_player_id(name)
    if idx is None:
      return False, 'invalid'
    if idx in self.winners:
      return False, 'invalid'
    self.loser = idx
    return True, None

  def set_han(self, text):
    if not re.match('^([1-9]|1[0-3])$', text):
      return False, 'invalid'
    self.han[-1] = text
    return True, None

  def get_valid_fu(self):
    lst = []
    if self.outcome == 'Tsumo':
      lst = [*TSUMO_VALUE[self.han[-1]]]
    else:
      lst = [*RON_VALUE[self.han[-1]]]

    lst = [int(i) for i in lst]
    lst.sort()
    lst = [str(i) for i in lst]
    return lst

  def set_fu(self, text):
    if not text in self.get_valid_fu():
      return False, 'invalid'
    self.fu[-1] = text
    return True, None

  def process_hand(self):
    if self.outcome in ['Tsumo', 'Nagashi Mangan']:
      self.process_tsumo_score_change()
    if self.outcome == 'Ron':
      self.process_ron_score_change()
    if self.outcome == 'Draw':
      self.process_draw_score_change()
    if self.outcome == 'Chombo':
      self.process_chombo_score_change()
    if self.outcome == 'Mid Game Draw':
      self.score_change.append([0, 0, 0, 0])

    self.process_riichi_stick_change()

    for i in range(len(self.winners)):
      score_change = self.score_change[i]
      self.value.append(score_change[self.winners[i]])

    while len(self.value) < len(self.score_change):
      self.value.append(0)
    while len(self.han) < len(self.score_change):
      self.han.append('0')
    while len(self.fu) < len(self.score_change):
      self.fu.append('0')
    while len(self.winners) < len(self.score_change):
      self.winners.append(0)

    self.final_score = [
        x+y for x, y in zip(self.get_total_score_change(), self.initial_score)]

    self.process_position()

  def process_position(self):
    self.position = [0.5, 0.5, 0.5, 0.5]
    for i in range(4):
      s = self.final_score[i]
      for x in self.final_score:
        if x == s:
          self.position[i] += 0.5
        if x > s:
          self.position[i] += 1

  def process_chombo_score_change(self):
    score_change = [0, 0, 0, 0]
    if self.chombo_option == 'Flat deduction':
      for i in range(len(self.chombo)):
        if self.chombo[i]:
          score_change[i] -= self.chombo_value

    if self.chombo_option == 'Payment to all':
      value_distributed = 0
      for i in range(len(self.chombo)):
        if self.chombo[i]:
          score_change[i] -= self.chombo_value*4
          value_distributed += self.chombo_value*4
      score_change = [x + int(value_distributed/4)
                      for x in score_change]
    self.score_change.append(score_change)

  def process_tsumo_score_change(self):
    winner = self.winners[0]
    score_change = [0, 0, 0, 0]
    if self.is_oya_win(winner):
      value = 40 if self.outcome == 'Nagashi Mangan' else self.get_tsumo_value(
          True)
      for i in range(4):
        if not i == winner:
          score_change[i] = -value
          if self.outcome == 'Tsumo':
            score_change[i] -= self.honba
      score_change[winner] = -sum(score_change)
    else:
      oya_value = 40 if self.outcome == 'Nagashi Mangan' else self.get_tsumo_value(
          True)
      value = 20 if self.outcome == 'Nagashi Mangan' else self.get_tsumo_value(
          False)
      for i in range(4):
        if not i == winner:
          score_change[i] = -value
          if self.outcome == 'Tsumo':
            score_change[i] -= self.honba
      score_change[self.round_num - 1] = -oya_value
      if self.outcome == 'Tsumo':
        score_change[self.round_num - 1] -= self.honba
      score_change[winner] = -sum(score_change)
    self.score_change.append(score_change)

  def get_tsumo_value(self, oya):
    return self.get_value_list(oya)[self.han[0]][self.fu[0]] if re.match(
        '^[1-4]$', self.han[0]) else self.get_value_list(oya)[self.han[0]]

  def process_ron_score_change(self):
    for i in range(len(self.winners)):
      winner = self.winners[i]
      score_change = [0, 0, 0, 0]

      if self.is_oya_win(winner):
        value = self.get_value_list(True)[self.han[i]][self.fu[i]] if re.match(
            '^[1-4]$', self.han[i]) else self.get_value_list(True)[self.han[i]]
      else:
        value = self.get_value_list(False)[self.han[i]][self.fu[i]] if re.match(
            '^[1-4]$', self.han[i]) else self.get_value_list(False)[self.han[i]]

      score_change[winner] = value + self.honba*3
      score_change[self.loser] = -value - self.honba*3
      self.score_change.append(score_change)

  def process_draw_score_change(self):
    score_change = [0, 0, 0, 0]

    num_tenpai = 0
    for t in self.tenpai:
      if t:
        num_tenpai += 1

    pos_value = 0
    neg_value = 0
    if num_tenpai == 1:
      pos_value = 30
      neg_value = -10
    if num_tenpai == 2:
      pos_value = 15
      neg_value = -15
    if num_tenpai == 3:
      pos_value = 10
      neg_value = -30

    for i in range(len(self.tenpai)):
      if self.tenpai[i]:
        score_change[i] = pos_value
      else:
        score_change[i] = neg_value

    self.score_change.append(score_change)

  def get_value_list(self, oya=False):
    scores = {
        'Tsumo': {
            'oya': {
                'not_kiriage': TSUMO_OYA_VALUE,
                'kiriage': TSUMO_OYA_KIRIAGE_VALUE
            },
            'ko': {
                'not_kiriage': TSUMO_VALUE,
                'kiriage': TSUMO_KIRIAGE_VALUE
            }
        },
        'Ron': {
            'oya': {
                'not_kiriage': RON_OYA_VALUE,
                'kiriage': RON_OYA_KIRIAGE_VALUE
            },
            'ko': {
                'not_kiriage': RON_VALUE,
                'kiriage': RON_KIRIAGE_VALUE
            }
        }
    }

    return scores[self.outcome]['oya' if oya else 'ko']['kiriage' if self.kiriage else 'not_kiriage']

  def is_oya_win(self, idx):
    return idx + 1 == self.round_num

  def process_riichi_stick_change(self):
    if self.outcome == 'Chombo':
      return

    score_change = [0, 0, 0, 0]
    for i in range(len(self.riichi)):
      if self.riichi[i]:
        self.pool += 10
        score_change[i] = -10

    if self.outcome == 'Tsumo' or self.outcome == 'Ron':
      winner = self.winners[0]
      score_change[winner] += self.pool
      self.pool = 0

    self.score_change[0] = [x+y for x,
                            y in zip(self.score_change[0], score_change)]

  def get_total_score_change(self):
    return [sum(i) for i in zip(*self.score_change)]

  def get_individual_outcome(self):
    if self.outcome == 'Draw':
      return [['Draw']*4]
    if self.outcome == 'Chombo':
      return [['Chombo']*4]
    if self.outcome == 'Tsumo':
      outcome = ['Tsumo-loss']*4
      outcome[self.winners[0]] = 'Tsumo'
      return [outcome]
    if self.outcome == 'Ron':
      final = []
      for i in range(len(self.winners)):
        outcome = ['']*4
        outcome[self.winners[i]] = 'Ron'
        outcome[self.loser] = 'Deal-in'
        final.append(outcome)
      return final
    if self.outcome == 'Mid Game Draw':
      return [['Mid Game Draw']*4]
    if self.outcome == 'Nagashi Mangan':
      outcome = ['Nagashi-loss']*4
      outcome[self.winners[0]] = 'Nagashi-win'
      return [outcome]

  def submit_hand(self, db, gid):
    player_id_list = self.players.get_id_list()
    oya = [False]*4
    oya[self.round_num - 1] = True
    ioutcome = self.get_individual_outcome()
    current_score = self.initial_score

    for i in range(len(self.score_change)):
      hid = db.set_hand_info([
          gid,
          self.hand_num,
          self.wind,
          self.round_num,
          self.honba,
          self.pool,
          self.outcome,
          self.han[i],
          self.fu[i],
          self.value[i]
      ])

      score_change = self.score_change[i]
      changed_score = [
          x+y for x, y in zip(score_change, current_score)]

      for j in range(4):
        db.set_hand_result([
            gid,
            hid,
            player_id_list[j],
            self.position[j],
            int(oya[j]),
            ioutcome[i][j],
            int(self.tenpai[j]),
            int(self.riichi[j]) if i == 0 else 0,
            current_score[j],
            changed_score[j],
            score_change[j],
            int(self.chombo[j]),
            self.riichi_order.index(j) if j in self.riichi_order else None
        ])

      current_score = changed_score


#############################################################################################
# Print
#############################################################################################


  def print_current_info(self):
    text = 'Hand Number: {}\n'.format(self.hand_num)
    text += 'Round: {}{}  {} Honba'.format(
        self.wind, self.round_num, self.honba)
    return text

  def print_change(self):
    text = 'Score Change:\n-----------------------------\n'
    text += print_name_score(self.players.get_name_list(),
                             self.get_total_score_change())
    return text

  def print_current_score(self):
    text = 'Current Score:\n-----------------------------\n'
    text += print_name_score(self.players.get_name_list(), self.final_score)
    text += '\nValue in pool: {}'.format(self.pool)
    return text

  def print_next_hand_info(self):
    wind, round_num, honba = self.get_next_wind_round_honba()
    return 'Next Hand:\n{}{}  {} Honba'.format(wind, round_num, honba)

  def print(self):
    return "{}\n\n{}\n\n{}\n\n{}".format(self.print_current_info(), self.print_change(), self.print_current_score(), self.print_next_hand_info())

  def print_settings(self):
    text = '{}\n\n'.format(self.print_current_info())
    player_names = self.players.get_name_list()

    if self.outcome == 'Chombo':
      text += 'Who Chombo:\n{}'.format(
          print_select_names(player_names, self.chombo))
      return text

    text += 'Outcome: {}\n\n'.format(self.outcome)

    if self.outcome == 'Mid Game Draw':
      return text

    if self.outcome == 'Draw':
      text += 'Who Tenpai:\n{}'.format(
          print_select_names(player_names, self.tenpai))
      text += '\n'
    if self.outcome == 'Nagashi Mangan':
      text += '{} Won Nagashi Mangan\n\n'.format(
          player_names[self.winners[0]]
      )
    if self.outcome == 'Tsumo':
      text += '{} Tsumo {} Han{}\n\n'.format(
          player_names[self.winners[0]], self.han[0], '' if self.fu[0] == '0' else ' {} Fu'.format(self.fu[0]))
    if self.outcome == 'Ron':
      for i in range(len(self.winners)):
        text += '{} Ron {} {} Han{}\n\n'.format(
            player_names[self.winners[i]], player_names[self.loser], self.han[i], '' if self.fu[i] == '0' else ' {} Fu'.format(
                self.fu[i])
        )

    text += 'Who Riichi:\n{}'.format(
        print_select_names_in_order(player_names, self.riichi_order))
    return text
