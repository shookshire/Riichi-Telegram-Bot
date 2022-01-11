from log_helper import logger

class GameState:
  _instance = None

  def __new__(cls):
    if cls._instance is None:
      logger.trace('Create new GameState')
      cls._instance = super(GameState, cls).__new__(cls)
      cls._instance.telegram_id = {}
    return cls._instance

  def update_state(self, players = [], hand = None):
    for p in players:
      self.telegram_id[p] = hand

  def get_game_state(self, id):
    if id in self.telegram_id and  self.telegram_id[id] is not None:
      return self.telegram_id[id].print()
    else:
      return 'User is currently not in a game'