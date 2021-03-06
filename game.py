
from datetime import datetime
from hand import Hand
from googlesheet import Googlesheets
from log_helper import logger
import push_msg
from config import MAIN_ADMIN
from threading import Thread, Lock

from helper_functions import print_end_game_result, print_game_confirmation, print_name_score


class Game:
  def __init__(self, players, recorded=False, location=None):
    self.initial_value = 250
    self.aka = 'Aka-Ari'
    self.uma = [15, 5, -5, -15]
    self.oka = 0
    self.chombo_value = 40
    self.chombo_option = 'Payment to all'
    self.kiriage = True
    self.multiple_ron = False
    self.starting_datetime = None
    self.hands = []
    self.penalty = [0, 0, 0, 0]
    self.current_hand = None
    self.timeout = False

    self.players = players
    self.recorded = recorded
    self.location = location

  def start_game(self):
    self.starting_datetime = datetime.now()

  def add_custom_uma(self, text):
    self.uma.append(int(text))

  def set_penalty(self, name, value):
    idx = self.players.get_player_id(name)
    if idx is None:
      return False, 'invalid'
    self.penalty[idx] = value
    return True, None

  def get_last_hand(self):
    return self.hands[-1] if self.hands else None

  def create_new_hand(self):
    self.current_hand = Hand(self.players, self.kiriage, self.chombo_option,
                             self.chombo_value, self.get_last_hand(), self.initial_value)

  def delete_last_hand(self):
    if len(self.hands):
      self.hands.pop()

  def drop_current_hand(self):
    self.current_hand = None

  def save_hand(self):
    self.current_hand.process_hand()
    self.hands.append(self.current_hand)
    self.current_hand = None

  def end_game(self, timeout=False):
    self.duration = divmod(
        (datetime.now() - self.starting_datetime).total_seconds(), 60)[0]
    self.timeout = timeout
    last_hand = self.get_last_hand()
    self.final_score = last_hand.final_score if not last_hand is None else [
        self.initial_value]*4
    self.position = last_hand.position if not last_hand is None else [2.5]*4

  def submit_game(self):
    thread = Thread(target=self.submit_game_thread)
    thread.start()

  def submit_game_thread(self):
    db = Googlesheets()
    gid = None
    try:
      logger.trace("Attempting to save game.")
      db.initialize()
      gid = db.set_game_info([
          self.starting_datetime.strftime("%d-%m-%Y"),
          self.starting_datetime.strftime('%H:%M:%S.%f')[:-4],
          self.initial_value,
          self.timeout,
          self.aka,
          self.uma[0],
          self.uma[1],
          self.uma[2],
          self.uma[3],
          self.oka,
          self.location.get_venue_id(),
          self.location.get_mode_id(),
          self.duration
      ])
      logger.trace("gid {} set game info completed".format(gid))

      player_id_list = self.players.get_id_list()
      for i in range(4):
        db.set_game_result([
            gid,
            i+1,
            player_id_list[i],
            self.final_score[i],
            self.position[i],
            self.penalty[i]
        ])
      logger.trace("gid {} set game result completed".format(gid))

      [hand.submit_hand(db, gid) for hand in self.hands]
      logger.trace("gid {} set hand info completed".format(gid))
      logger.trace(
          "gid {} have been saved. Timeout={}".format(gid, self.timeout))

      final_score_text = print_end_game_result(self.players.get_name_list(
      ), self.final_score, self.position, self.initial_value, self.uma)
      message = print_game_confirmation(gid, '`{}`'.format(final_score_text))
      self.players.notify_players(message)
    except Exception as e:
      logger.error('Failed to save game.')
      logger.error(e)
      for admin_id in MAIN_ADMIN:
        if not gid is None:
          push_msg.send_msg(
              "Notice to admins: The following gid have failed halfway through the submission please delete these games manually: {}".format(gid), admin_id)
        push_msg.send_msg(
            "Notice to admins: A game with the following players have failed to be submitted successfully even after 5 retries: {}".format(', '.join(self.players.get_name_list())), admin_id)
    finally:
      db.release()

  def print_current_game_state(self):
    last_hand = self.get_last_hand()
    if last_hand is None:
      text = 'Current score:\n-----------------------------\n'
      text += print_name_score(self.players.get_name_list(),
                               [self.initial_value]*4)
      text += '\nValue in pool: 0'
      return text
    return last_hand.print()

  def print_game_settings(self):
    text = 'Settings:\n'
    text += '-----------------------------\n'
    text += 'Initial Value:  | {}\n'.format(self.initial_value)
    text += 'Aka:            | {}\n'.format(self.aka)
    text += 'Uma:            | {},{},{},{}\n'.format(
        self.uma[0], self.uma[1], self.uma[2], self.uma[3])
    text += 'Oka:            | {}\n'.format(self.oka)
    text += 'Chombo Value:   | {}\n'.format(self.chombo_value)
    text += 'Chombo Option:  | {}\n'.format(self.chombo_option)
    text += 'Kiriage Mangan: | {}\n'.format(
        'Yes' if self.kiriage else 'No')
    text += 'Multiple Ron: 	 | {}\n'.format(
        'Yes' if self.multiple_ron else 'No')
    return text
