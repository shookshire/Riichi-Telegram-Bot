import re

from datetime import datetime
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import push_msg
from helper_functions import print_end_game_result, print_game_confirmation, print_select_names, print_select_names_in_order
from googlesheet import Googlesheets
from log_helper import catch_error, logger
from config import DB_CONFIG, SPREADSHEET_CONFIG, ADMIN
from threading import Thread, Lock

from constants import SEAT_NAME, BLOCKED_NAMES

# Pre-settings for recorded game
from constants import SET_RECORDED_GAME

# Set host and season
from constants import SET_VENUE, SET_MODE, CONFIRM_VENUE_MODE
# Setting of players
from constants import SET_PLAYER_NAME, CONFIRM_PLAYER_NAME

# Setting game settings
from constants import SELECT_EDIT_SETTINGS, SET_INITIAL_VALUE, SET_AKA, SET_UMA, SET_CUSTOM_UMA, SET_CHOMBO_VALUE, SET_OKA, SET_CHOMBO_PAYMENT_OPTION, SET_KIRIAGE, SET_ATAMAHANE, CONFIRM_GAME_SETTINGS, SELECT_RULE_SET

# Updating new hand
from constants import SELECT_NEXT_COMMAND, CANCEL_GAME, DELETE_LAST_HAND, SET_HAND_OUTCOME, SET_WINNER, SET_LOSER, SET_DRAW_TENPAI, SET_HAN, SET_FU, SET_RIICHI, SET_CHOMBO, PROCESS_HAND, MULTIPLE_RON

# Confirm game end
from constants import CONFIRM_GAME_END, SELECT_HAVE_PENALTY, SET_PENALTY_PLAYER, SET_PENALTY_VALUE, COMPLETE_GAME

# Set final score
from constants import SET_PLAYER_FINAL_SCORE

from players import Players
from location import Location
from game import Game
from game_state import GameState

from constants import UNIVERSAL_MID


def format_text_for_telegram(str):
  return '`' + str + '`'


@catch_error
def helper(update, context):

  update.message.reply_text(
      "Akako records your every hand played during the game and give you interesting statistical insights! Only for registered Singaporean Riichi players.\n\n"
      + "Just follow a few simple steps below!\n"
      + "1. You can register at https://sgriichimahjong.com/join-sgriichi/\n"
      + "2. You will be asked for your telegram id number. Type /telegramid , copy and paste into the form.\n"
      + "3. Upon filling up the 2 forms, wait for 0.5 working day or contact @MrFeng for the bot to update with your registered information.\n"
      + "4. Once updated, type /myinfo to retrieve your player id and registered player name. Please remember them.\n"
      + "5. Type /riichi to start using it! Only 1 person of the table will record. If you are not recording, provide your player id or player name to the person recording.\n"
      + "6. Your games recorded will be tabulated at https://sgriichimahjong.com/results/\n\n"
      + "List of Akako functions:\n"
      + "/riichi : Start a new riichi score tracker. Game data for recorded games will be automatically stored to SgRiichi server.\n"
      +
        "/score: Displays the status of your current game. (If you are currently in game)\n"
      + "/myinfo: Returns your SgRiichi id if your telegram id have been registered in SgRiichi's database.\n"
      + "/help: Display this starting message\n"
      + "/quit: Quit current game. Game data will not be recorded.\n"
      + "/telegramid: Returns your telegram id number.\n"
      + "/mcr: Start a new MCR score tracker. Game data are NOT recorded. No registration required.")

  return ConversationHandler.END


@catch_error
def get_googlesheet_data(update, context):
  bot_data = context.bot_data
  if SPREADSHEET_CONFIG['in_use'] and update.message.chat.id in ADMIN:
    googlesheet = Googlesheets()
    bot_data['player_list'] = googlesheet.get_player_list()
    bot_data['venue_list'] = googlesheet.get_venue_list()
    bot_data['mode_list'] = googlesheet.get_mode_list()
    bot_data['rules_list'] = googlesheet.get_rules_list()
    update.message.reply_text('finish updating data')

  logger.trace('Data has been populated.')

  return ConversationHandler.END


@catch_error
def get_telegram_id(update, context):
  update.message.reply_text('telegram id:')
  update.message.reply_text('{}'.format(update.message.chat.id))
  return ConversationHandler.END


@catch_error
def get_sgriichi_id(update, context):
  bot_data = context.bot_data
  telegram_id = update.message.chat.id
  player_list = bot_data['player_list']

  filtered = list(
      filter(lambda x: x['telegram_id'] == telegram_id, player_list))
  if len(filtered):
    update.message.reply_text(
        'Your player id is "{}"\n'.format(filtered[0]['pid'])
        + 'Your player name is "{}"\n'.format(filtered[0]['name'])
        + 'Please remember either one of this during inputting player name when using Akako.'
    )
  else:
    update.message.reply_text(
        'Your telegram id has not been registered. If you have already signed up with SgRiichi, please contact @MrFeng or other SgRiichi admins.')

  return ConversationHandler.END


@catch_error
def start_new_game(update, context):
  user_data = context.user_data
  user_data['recorded'] = False

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Do you want this game to be recorded?`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_RECORDED_GAME


@catch_error
def set_not_recorded_Game(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  user_data['recorded'] = False
  user_data['location'] = None
  user_data['players'] = Players(bot_data['player_list'], True)

  update.message.reply_text(
      '`Please enter {} player name:`'.format(SEAT_NAME[0]),
      parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME


@catch_error
def set_recorded_game(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  user_data['recorded'] = True

  location = Location(bot_data['venue_list'], bot_data['mode_list'])
  user_data['location'] = location

  reply_keyboard = [[h['name'] for h in location.venue_list[i:i+2]]
                    for i in range(0, len(location.venue_list), 2)]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Please select the venue of this game`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_VENUE


@catch_error
def set_game_venue(update, context):
  user_data = context.user_data
  text = update.message.text
  location = user_data['location']

  success, _ = location.set_venue(text)

  if not success:
    reply_keyboard = [[h['name'] for h in location.venue_list[i:i+2]]
                      for i in range(0, len(location.venue_list), 2)]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        '`Invalid venue name inputted. Please select a valid venue name`',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=markup)

    return SET_VENUE

  mode_list = location.get_valid_mode()

  reply_keyboard = [[h['name'] for h in mode_list[i:i+2]]
                    for i in range(0, len(mode_list), 2)]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Please select the mode for this game`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_MODE


@catch_error
def set_game_mode(update, context):
  user_data = context.user_data
  text = update.message.text
  location = user_data['location']

  success, _ = location.set_mode(text)

  if not success:
    mode_list = location.get_valid_mode()
    reply_keyboard = [[h['name'] for h in mode_list[i:i+2]]
                      for i in range(0, len(mode_list), 2)]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        '`Invalid mode inputted. Please select a valid mode name`',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=markup)

    return SET_MODE

  reply_keyboard = [['Confirm', 'Exit']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Venue: {}\nMode: {}\n\nIs this correct?`'.format(
          location.get_venue_name(), location.get_mode_name()),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return CONFIRM_VENUE_MODE


@catch_error
def confirm_venue_mode(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  user_data['players'] = Players(bot_data['player_list'], False)
  update.message.reply_text(
      '`Please enter {} player name or id number:`'.format(SEAT_NAME[0]),
      parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME


@catch_error
def exit_venue_mode(update, context):
  user_data = context.user_data

  update.message.reply_text(
      "`Game settings have been discarded`", parse_mode=ParseMode.MARKDOWN_V2)
  user_data.clear()
  return ConversationHandler.END


@catch_error
def set_player_by_name(update, context):
  user_data = context.user_data
  text = update.message.text
  players = user_data['players']

  success, error = players.add_player(text)

  if not success:
    if error == 'reserved':
      update.message.reply_text("`This player name is not allowed`",
                                parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME
    if error == 'invalid':
      update.message.reply_text("`Please enter a valid name`",
                                parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME
    if error == 'duplicate':
      update.message.reply_text("`This player has already been entered`",
                                parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME

  if players.count() < 4:
    update.message.reply_text("`Player Name {} entered\n"
                              "Please enter {} player's name`".format(
                                  players.get_name_list()[-1], SEAT_NAME[players.count()]),
                              parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME

  reply_keyboard = [['Proceed', 'Re-enter Names']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
  player_names = players.get_name_list()
  update.message.reply_text(
      "`East : {}\n"
      "South: {}\n"
      "West : {}\n"
      "North: {}\n\n"
      "Is this ok?`".
      format(player_names[0],
             player_names[1],
             player_names[2],
             player_names[3]),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)
  return CONFIRM_PLAYER_NAME


@catch_error
def set_player_by_id(update, context):
  user_data = context.user_data
  text = update.message.text
  players = user_data['players']

  if not user_data['recorded']:
    update.message.reply_text("`Please enter a valid name`",
                              parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME

  success, error = players.add_player(None, text)

  if not success:
    if error == 'invalid':
      update.message.reply_text("`Please enter a valid id`",
                                parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME
    if error == 'duplicate':
      update.message.reply_text("`This player has already been entered`",
                                parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME

  if players.count() < 4:
    update.message.reply_text("`Player Name {} entered\n"
                              "Please enter {} player's name`".format(
                                  players.get_name_list()[-1], SEAT_NAME[players.count()]),
                              parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME

  reply_keyboard = [['Proceed', 'Re-enter Names']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
  player_names = players.get_name_list()
  update.message.reply_text(
      "`East : {}\n"
      "South: {}\n"
      "West : {}\n"
      "North: {}\n\n"
      "Is this ok?`".
      format(player_names[0],
             player_names[1],
             player_names[2],
             player_names[3]),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)
  return CONFIRM_PLAYER_NAME


@ catch_error
def confirm_player_name(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  text = update.message.text

  if text == "Re-enter Names":
    user_data['players'] = Players(
        bot_data['player_list'], not user_data['recorded'])

    update.message.reply_text(
        '`Please enter {} player name or id number:`'.format(SEAT_NAME[0]),
        parse_mode=ParseMode.MARKDOWN_V2)

    return SET_PLAYER_NAME

  game = Game(
      user_data['players'], user_data['recorded'], user_data['location'])
  user_data['game'] = game

  if not user_data['recorded']:
    return return_select_edit_settings(update, game)

  rules_list = bot_data['rules_list']
  mode_id = user_data['location'].get_mode_id()

  return return_select_rule_set(update, rules_list, mode_id)


def return_select_rule_set(update, rules_list, mode_id):
  reply_keyboard = list(
      filter(lambda x: x['mid'] == mode_id or x['mid'] == 0, rules_list))
  reply_keyboard.append({'label': 'Custom'})

  reply_keyboard = [[h['label'] for h in reply_keyboard[i:i+2]]
                    for i in range(0, len(reply_keyboard), 2)]

  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Please select a rule set:`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SELECT_RULE_SET


def return_select_edit_settings(update, game):
  reply_keyboard = [['Done'], ['Kiriage Mangan', 'Multiple Ron'], [
      'Initial Value', 'Aka'], ['Uma', 'Oka'], ['Chombo Value', 'Chombo Options']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Which settings would you like to edit?\n\n{}`'.format(
          game.print_game_settings()),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SELECT_EDIT_SETTINGS


@catch_error
def select_rules(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  game = user_data['game']
  text = update.message.text
  rules_list = bot_data['rules_list']

  if text == 'Custom':
    return return_select_edit_settings(update, game)

  find_rule = list(filter(lambda x: x['label'] == text, rules_list))
  if len(find_rule) == 0:
    mode_id = user_data['location'].get_mode_id()
    return return_select_rule_set(update, rules_list, mode_id)

  rule = find_rule[0]

  game.initial_value = rule['initial_value']
  game.aka = rule['aka']
  game.uma = rule['uma']
  game.oka = rule['oka']
  game.chombo_value = rule['chombo_value']
  game.chombo_option = rule['chombo_option']
  game.kiriage = rule['kiriage']
  game.multiple_ron = rule['multiple_ron']

  return return_confirm_game_settings(update, game)


@ catch_error
def select_edit_atamahane(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Is multiple ron allowed?:`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_ATAMAHANE


@ catch_error
def set_atamahane(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.multiple_ron = text == 'Yes'

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_kiriage_mangan(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Is there kiriage mangan?:`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_KIRIAGE


@ catch_error
def set_kiriage_mangan(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.kiriage = text == 'Yes'

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_initial_value(update, context):
  reply_keyboard = [['250', '300']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Please select the initial value:`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_INITIAL_VALUE


@ catch_error
def set_initial_value(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.initial_value = int(text)

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_aka(update, context):
  reply_keyboard = [['Aka-Ari', 'Aka-Nashi']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Please select the options for aka:`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_AKA


@ catch_error
def set_aka(update, context):
  text = update.message.text
  user_data = context.user_data

  game = user_data['game']
  game.aka = text

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_uma(update, context):
  reply_keyboard = [['15/5', '20/10'], ['Set custom uma']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Please select options for uma:`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_UMA


@ catch_error
def set_default_uma(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']

  if text == "15/5":
    game.uma = [15, 5, -5, -15]

  if text == "20/10":
    game.uma = [20, 10, -10, -20]

  return return_select_edit_settings(update, game)


@ catch_error
def select_custom_uma(update, context):
  user_data = context.user_data

  game = user_data['game']
  game.uma = []

  update.message.reply_text(
      '`Please enter uma for position 1`',
      parse_mode=ParseMode.MARKDOWN_V2)

  return SET_CUSTOM_UMA


@ catch_error
def set_custom_uma(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.add_custom_uma(text)

  if len(game.uma) < 4:
    update.message.reply_text("`Please enter uma for position {}`".format(len(game.uma) + 1),
                              parse_mode=ParseMode.MARKDOWN_V2)
    return SET_CUSTOM_UMA

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_oka(update, context):
  update.message.reply_text(
      '`Please enter oka amount`',
      parse_mode=ParseMode.MARKDOWN_V2)

  return SET_OKA


@ catch_error
def set_oka(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.oka = int(text)

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_chombo_value(update, context):
  update.message.reply_text(
      '`Please enter amount of points to deduct when someone chombo\nNote that the value will not be split among other players.`',
      parse_mode=ParseMode.MARKDOWN_V2)

  return SET_CHOMBO_VALUE


@ catch_error
def set_chombo_value(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.chombo_value = int(text)

  return return_select_edit_settings(update, game)


@ catch_error
def select_edit_chombo_payment_option(update, context):
  reply_keyboard = [['Payment to all', 'Flat deduction']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Please choose the option for chombo:\n\n`'
      + '`Payment to all: The combo value set will be payed to each of the other player eg. chombo value 40, the player who chombo will 1120 while other 3 players +40\n\n`'
      + '`Flat deduction: The value set in chombo value will be deducted from the combo player, the others will not gain any points`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_CHOMBO_PAYMENT_OPTION


@ catch_error
def set_chombo_payment_option(update, context):
  user_data = context.user_data
  text = update.message.text

  game = user_data['game']
  game.chombo_option = text

  return return_select_edit_settings(update, game)


def return_confirm_game_settings(update, game):
  reply_keyboard = [['Start game', 'Discard game'], ['Enter Final Score']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`{}\n\nIs the game settings ok?`'.format(game.print_game_settings()),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return CONFIRM_GAME_SETTINGS


@ catch_error
def select_edit_done(update, context):
  user_data = context.user_data
  game = user_data['game']
  return return_confirm_game_settings(update, game)


@ catch_error
def get_my_score(update, context):
  telegram_id = update.message.chat.id

  sample = GameState()
  update.message.reply_text(
      '`{}`'.format(sample.get_game_state(telegram_id)),
      parse_mode=ParseMode.MARKDOWN_V2)

  return ConversationHandler.END


#############################################################################################
# GAme start
#############################################################################################

def return_next_command(update, text):
  reply_keyboard = [['New Hand', 'End Game'],
                    ['Delete Last Hand', 'Cancel Game']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      text,
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SELECT_NEXT_COMMAND


@ catch_error
def start_game(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.start_game()

  return return_next_command(update, format_text_for_telegram(game.print_current_game_state()))


def return_next_player_score_command(update, game, text=''):
  player_num = len(game.final_score)
  player_name = game.players.get_name_list()[player_num]

  update.message.reply_text(
      "`{}Please enter {}'s score`".format(text, player_name),
      parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_FINAL_SCORE


@catch_error
def start_final_score_only(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.start_game()
  game.final_score_only = True

  return return_next_player_score_command(update, game, "All scores are to be inputted in hundreds (45k = input 450)\n\n")


@catch_error
def set_final_score(update, context):
  user_data = context.user_data
  game = user_data['game']
  text = update.message.text

  num = game.set_final_score(text)
  if num < 4:
    return return_next_player_score_command(update, game)

  if not game.verify_final_score():
    total_input_score = sum(game.final_score)
    game.reset_final_score()
    return return_next_player_score_command(update, game, "Total score inputted is {}. It does not tally. Please re-enter the final scores.\n\nAll scores are to be inputted in hundreds (45k = input 450)\n\n".format(total_input_score))

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      format_text_for_telegram('Is the score correct?\n\n{}'.format(
          game.print_final_score())),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return CONFIRM_GAME_END


@ catch_error
def discard_game_settings(update, context):
  user_data = context.user_data
  update.message.reply_text("`Game has been discarded.`",
                            parse_mode=ParseMode.MARKDOWN_V2)

  user_data.clear()
  return ConversationHandler.END


@ catch_error
def add_new_hand(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.create_new_hand()

  return return_4_player_done_option(update, game.players.get_name_list(), SET_RIICHI, '`Who riichi first?`')


def return_4_player_option(update, player_names, return_state, text):
  reply_keyboard = [
      ['{}'.format(player_names[0]), '{}'.format(player_names[1])],
      ['{}'.format(player_names[2]), '{}'.format(player_names[3])],
      ['Drop Current Hand']
  ]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      text,
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return return_state


def return_4_player_done_option(update, player_names, return_state, text, drop_current_hand_option=True):
  reply_keyboard = [
      ['{}'.format(player_names[0]), '{}'.format(player_names[1])],
      ['{}'.format(player_names[2]), '{}'.format(player_names[3])]
  ]
  if drop_current_hand_option:
    reply_keyboard.append(['Done', 'Drop Current Hand'])
  else:
    reply_keyboard.append(['Done'])
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      text,
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return return_state


@ catch_error
def set_hand_outcome(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand
  player_names = game.players.get_name_list()

  hand.outcome = text

  if text == 'Mid Game Draw':
    reply_keyboard = [['Save', 'Discard']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        '`{}\nIs this setting ok?`'.format(hand.print_settings()),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=markup
    )

    return PROCESS_HAND

  if text == 'Draw':
    return return_4_player_done_option(update, player_names, SET_DRAW_TENPAI, '`Who is in Tenpai?`')

  if text == 'Chombo':
    return return_4_player_done_option(update, player_names, SET_CHOMBO, '`Who Chombo?`')

  return return_4_player_option(update, player_names, SET_WINNER, '`Who Won?`')


def return_set_han(update):
  reply_keyboard = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['10', '11', '12', '13']
  ]
  reply_keyboard.append(['Drop Current Hand'])
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`How many Han?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup
  )

  return SET_HAN


@ catch_error
def set_winner(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand
  player_names = game.players.get_name_list()

  success, error = hand.set_winner(text)

  if not success:
    if error == 'invalid':
      return return_4_player_option(update, player_names, SET_WINNER, '`Invalid player selected\nPlease select a valid player name`')
    if error == 'duplicate':
      return return_4_player_option(update, player_names, SET_WINNER, '`This player have already been selected. Please select another player.`')

  if not hand.loser is None:
    return return_set_han(update)

  if hand.outcome == "Tsumo":
    return return_set_han(update)

  if hand.outcome == 'Nagashi Mangan':
    return return_4_player_done_option(update, player_names, SET_DRAW_TENPAI, '`Who is in Tenpai?`')

  return return_4_player_option(update, player_names, SET_LOSER, '`Who dealt in?`')


@ catch_error
def set_loser(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand
  player_names = game.players.get_name_list()

  success, _ = hand.set_loser(text)

  if not success:
    return return_4_player_option(update, player_names, SET_LOSER, '`Invalid player selected\nPlease select a valid player name`')

  return return_set_han(update)


def return_set_fu(update, fu_list, text):
  reply_keyboard = [fu_list[i:i+3] for i in range(0, len(fu_list), 3)]
  reply_keyboard.append(['Drop Current Hand'])
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      text,
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SET_FU


@ catch_error
def set_han(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand

  hand.set_han(text)

  if re.match('^[1-4]$', text):
    fu_list = hand.get_valid_fu()
    return return_set_fu(update, fu_list, '`How many Fu?`')

  if hand.outcome == 'Ron' and game.multiple_ron and len(hand.winners) < 3:
    reply_keyboard = [['Yes', 'No']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        '`Did anyone else Ron?`',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=markup)

    return MULTIPLE_RON

  return return_save_discard_hand_option(update, hand)


@ catch_error
def set_fu(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand

  success, _ = hand.set_fu(text)
  fu_list = hand.get_valid_fu()

  if not success:
    return return_set_fu(update, fu_list, '`Invalid Fu Selected\nPlease choose a valid Fu`')

  if hand.outcome == 'Ron' and game.multiple_ron and len(hand.winners) < 3:
    reply_keyboard = [['Yes', 'No']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        '`Did anyone else Ron?`',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=markup)

    return MULTIPLE_RON

  return return_save_discard_hand_option(update, hand)


@ catch_error
def set_draw_tenpai(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand
  player_names = game.players.get_name_list()

  success, _ = hand.toggle_tenpai(text)

  if not success:
    return return_4_player_done_option(update, player_names, SET_DRAW_TENPAI, '`Invalid player name entered\nPlease enter a valid player name`')

  return return_4_player_done_option(update, player_names, SET_DRAW_TENPAI,
                                     '`Players who are in tenpai:\n(Click on the player\'s name again to remove him/her from the list)\n-----------------------------\n{}\nWho is in Tenpai?`'.format(print_select_names(player_names, hand.tenpai)))


@ catch_error
def set_draw_tenpai_done(update, context):
  user_data = context.user_data
  hand = user_data['game'].current_hand

  return return_save_discard_hand_option(update, hand)


@ catch_error
def set_riichi(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand
  player_names = game.players.get_name_list()

  success, _ = hand.toggle_riichi(text)

  if not success:
    return return_4_player_done_option(update, player_names, SET_RIICHI, '`Invalid player name entered\nPlease enter a valid player name`')

  return return_4_player_done_option(update, player_names, SET_RIICHI,
                                     '`Order of players who riichi:\n(Click on the player\'s name again to remove him/her from the list)\n-----------------------------\n{}\nWho riichi next?`'.format(print_select_names_in_order(player_names, hand.riichi_order)))


def return_save_discard_hand_option(update, hand):
  reply_keyboard = [['Save', 'Discard']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`{}\nIs this setting ok?`'.format(hand.print_settings()),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return PROCESS_HAND


@ catch_error
def set_riichi_done(update, context):
  reply_keyboard = [['Tsumo', 'Ron'], [
      'Draw', 'Mid Game Draw'], ['Nagashi Mangan', 'Chombo']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`What is the hand outcome?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)
  return SET_HAND_OUTCOME


@ catch_error
def set_chombo(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  hand = game.current_hand
  player_names = game.players.get_name_list()

  success, _ = hand.toggle_chombo(text)

  if not success:
    return return_4_player_done_option(update, player_names, SET_CHOMBO, '`Invalid player name entered\nPlease enter a valid player name`')

  return return_4_player_done_option(update, player_names, SET_CHOMBO,
                                     '`Players who Chombo:\n(Click on the player\'s name again to remove him/her from the list)\n-----------------------------\n{}\nWho Chombo?`'.format(print_select_names(player_names, hand.chombo)))


@ catch_error
def set_chombo_done(update, context):
  user_data = context.user_data
  game = user_data['game']
  hand = game.current_hand

  reply_keyboard = [['Save', 'Discard']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`{}\nIs this setting ok?`'.format(hand.print_settings()),
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return PROCESS_HAND


@ catch_error
def discard_hand(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.current_hand = None

  return return_next_command(update, '`Hand have been discarded\n{}\n\nPlease select an option:`'.format(game.print_current_game_state()))


@ catch_error
def save_hand(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.save_hand()

  return return_next_command(update, '`{}\n\nPlease select an option:`'.format(game.print_current_game_state()))


@ catch_error
def confirm_multiple_ron(update, context):
  user_data = context.user_data
  player_names = user_data['game'].players.get_name_list()

  return return_4_player_option(update, player_names, SET_WINNER, '`Who Won?`')


@ catch_error
def no_multiple_ron(update, context):
  user_data = context.user_data
  hand = user_data['game'].current_hand
  return return_save_discard_hand_option(update, hand)


@ catch_error
def drop_current_hand(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.drop_current_hand()

  return return_next_command(update, '`{}\n\nPlease select an option:`'.format(game.print_current_game_state()))


@ catch_error
def end_game(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`End Game?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return CONFIRM_GAME_END


@ catch_error
def confirm_game_end(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Are there any penalties?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return SELECT_HAVE_PENALTY


@ catch_error
def select_have_penalty(update, context):
  user_data = context.user_data
  game = user_data['game']
  player_names = game.players.get_name_list()

  return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, '`Penalty:\n-----------------------------\n{}\nWho has a penalty?`'.format(print_select_names(player_names, game.penalty)), False)


@ catch_error
def set_penalty_player(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['chosen'] = text

  update.message.reply_text('`Please enter the penalty amount for {} (without the negative sign)`'.format(text),
                            parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PENALTY_VALUE


@ catch_error
def set_penalty_value(update, context):
  user_data = context.user_data
  text = update.message.text
  game = user_data['game']
  player_names = game.players.get_name_list()

  value = int(text)
  success, _ = game.set_penalty(user_data['chosen'], value)
  del user_data['chosen']

  if not success:
    return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, '`Penalty:\n-----------------------------\n{}\nInvalid name entered.\nWho has a penalty?`'.format(print_select_names(player_names, game.penalty)), False)

  return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, '`Penalty:\n-----------------------------\n{}\nWho has a penalty?`'.format(print_select_names(player_names, game.penalty)), False)


@ catch_error
def confirm_penalty_done(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      '`Have you completed setting the penalty?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return COMPLETE_GAME


@ catch_error
def return_to_next_command(update, context):
  user_data = context.user_data
  game = user_data['game']

  if game.final_score_only:
    game.reset_final_score()
    return return_next_player_score_command(update, game, "All scores are to be inputted in hundreds (45k = input 450)\n\n")

  return return_next_command(update, format_text_for_telegram(game.print_current_game_state()))


@ catch_error
def save_complete_game(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.end_game()
  update.message.reply_text(
      '`Game have been completed.\n\n{}`'.format(print_end_game_result(
          game.players.get_name_list(), game.final_score, game.position, game.initial_value, game.uma)),
      parse_mode=ParseMode.MARKDOWN_V2)
  if game.recorded:
    update.message.reply_text(
        '`The game result is being submitted`',
        parse_mode=ParseMode.MARKDOWN_V2)
    game.submit_game()

  user_data.clear()
  return ConversationHandler.END


def confirm_delete_last_hand(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Delete last hand?`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return DELETE_LAST_HAND


@ catch_error
def delete_last_hand(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.delete_last_hand()

  return return_next_command(update, '`{}\n\nPlease select an option:`'.format(game.print_current_game_state()))


@ catch_error
def confirm_cancel_game(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
      "`Cancel Game?\nThe game's result will not be recorded.`",
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

  return CANCEL_GAME


@ catch_error
def quit(update, context):
  user_data = context.user_data

  if 'game' in user_data:
    game_state = GameState()
    game_state.update_state(user_data['game'].players.get_telegram_list())

  update.message.reply_text(
      "`User has exited successfully`", parse_mode=ParseMode.MARKDOWN_V2)
  user_data.clear()
  return ConversationHandler.END


@ catch_error
def timeout(update, context):
  user_data = context.user_data
  game = user_data['game']

  game.end_game(True)
  if game.recorded:
    game.submit_game()

  user_data.clear()
  return ConversationHandler.END
