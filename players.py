
import string
import push_msg
from log_helper import logger


def handle_name(name):
  return string.capwords(name.strip()) if not name is None else None


class Players:
  reserved_names = ['Done', 'Quit']

  def __init__(self, players_list=None, free_naming=False):
    self.players = []
    self.players_list = players_list
    self.free_naming = free_naming

  def count(self):
    return len(self.players)

  def get_player_details(self, name=None, id=None):
    if not id is None:
      id = int(id)
    filtered = list(
        filter(lambda x: (x['name'] == handle_name(name) or x['pid'] == id), self.players_list))
    return filtered[0] if len(filtered) else None

  def check_duplicate_player(self, player):
    return player in self.players

  def check_reserved_name(self, name):
    return handle_name(name) in self.reserved_names

  def add_player(self, name=None, id=None):
    if self.check_reserved_name(name):
      return False, 'reserved'

    if self.free_naming:
      if name is None:
        return False, 'invalid'
      player = {'name': handle_name(name), 'pid': 0}
    else:
      player = self.get_player_details(name, id)
      if player is None:
        return False, 'invalid'
      if self.check_duplicate_player(player):
        return False, 'duplicate'

    self.players.append(player)
    return True, None

  def get_name_list(self):
    return [p['name'] for p in self.players]

  def get_id_list(self):
    return [p['pid'] for p in self.players]

  def get_telegram_list(self):
    return [p['telegram_id'] for p in self.players]

  def get_player_id(self, name):
    name = handle_name(name)
    name_list = self.get_name_list()
    return name_list.index(name) if name in name_list else None

  def notify_players(self, message):
    for telegram_id in self.get_telegram_list():
      try:
        push_msg.send_msg(message, telegram_id)
        logger.trace('Successfully send game confirmation to {}'.format(
            telegram_id))
      except Exception as e:
        logger.error('Failed to send game confirmation to {}'.format(
            telegram_id))
        logger.error(e)
