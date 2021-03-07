import helper_functions as func
from telegram import ReplyKeyboardMarkup, ParseMode
from log_helper import logger
import push_msg
import copy


def check_valid_name_from_list(name, player_list):
  filtered = list(filter(lambda x: x['name'] == name, player_list))
  return filtered[0] if len(filtered) else None


def check_valid_id_from_list(pid, player_list):
  filtered = list(filter(lambda x: x['pid'] == pid, player_list))
  return filtered[0] if len(filtered) else None


def filter_mode_by_bid(mode_list, vid):
  return list(filter(lambda x: x['vid'] == vid, mode_list))


def log_game_data(game):
  game_for_logging = copy.copy(game)
  game_for_logging.pop('mode_list', None)
  game_for_logging.pop('venue_list', None)
  logger.trace("Game data: {}".format(game_for_logging))


def print_final_outcome(update, game, gid):
  players = game['players']
  player_names = func.get_all_player_name(players)

  final_score_text = func.print_end_game_result(
      player_names, game['final score'], game['position'], game['initial value'])

  for player in players:
    if player['telegram_id']:
      try:
        push_msg.send_msg(func.print_game_confirmation(
            gid, final_score_text), player['telegram_id'])
        logger.trace("Successfully send game confirmation to {}".format(
            player['telegram_id']))
      except Exception as e:
        logger.error("Failed to send game confirmation to {}".format(
            player['telegram_id']))
        logger.error(e)
