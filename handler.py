import re
import numpy as np
import string

from datetime import datetime
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import push_msg
import helper_functions as func
import googlesheet_helper_func as gfunc
import db
import googlesheet
from constants import *
from log_helper import catch_error, logger
from config import DB_CONFIG, SPREADSHEET_CONFIG, ADMIN
from threading import Thread, Lock

@catch_error
def helper(update, context):

  update.message.reply_text(
    "For registration and other queries, please contact @MrFeng\n\n"
    +"/riichi : Start a new riichi score tracker. Game data for recorded games will be automatically stored to SgRiichi server.\n\n"
    +"/mcr: Start a new MCR score tracker. Game data are NOT recorded.\n\n"
    # +"/record : Save final game score to SgRiichi server.\n\n"
    +"/get_telegram_id: Returns your telegram id number.\n\n"
    +"/get_sgriichi_id: Returns your SgRiichi id if your telegram id have been registered in SgRiichi's database.\n\n"
    +"/quit: Quit current game. Game data will not be recorded.")

  return ConversationHandler.END

@catch_error
def get_googlesheet_data(update, context):
  bot_data = context.bot_data
  if SPREADSHEET_CONFIG['in_use'] and update.message.chat.id in ADMIN:
    bot_data['player_list'] = googlesheet.get_player_list()
    bot_data['venue_list'] = googlesheet.get_venue_list()
    bot_data['mode_list'] = googlesheet.get_mode_list()
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

  filtered = list(filter(lambda x: x['telegram_id'] == telegram_id, player_list))
  if len(filtered):
    update.message.reply_text('SgRiichi id:')
    update.message.reply_text('{}'.format(filtered[0]['pid']))
  else:
    update.message.reply_text('Your telegram id has not been registered. If you have already signed up with SgRiichi, please contact @MrFeng or other SgRiichi admins.')

  return ConversationHandler.END



@catch_error
def start_new_game(update, context):
  user_data = context.user_data
  user_data['result only'] = False
  user_data['players'] = []

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Please select if this game will be recorded by SgRiichi:\nDo note that only games played by 4 registered SgRiichi players can be recorded`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_RECORDED_GAME

@catch_error
def start_input_game_result(update, context):
  user_data = context.user_data
  user_data['result only'] = True
  user_data['recorded'] = True
  user_data['players'] = []
  user_data['final score'] = []
  user_data['penalty'] = [0,0,0,0]
  user_data['final pool'] = 0

  update.message.reply_text(
    '`Please enter {} player name or id number:`'.format(SEAT_NAME[0]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME


@catch_error
def set_recorded_game(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  user_data['recorded'] = True

  if DB_CONFIG['in_use']:
    venue_list = db.get_all_venue()
  elif SPREADSHEET_CONFIG['in_use']:
    venue_list = bot_data['venue_list']
  user_data['venue_list'] = venue_list

  reply_keyboard = [[h['name'] for h in venue_list[i:i+2]] for i in range(0, len(venue_list), 2)]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Please select the venue of this game`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_VENUE

@catch_error
def set_not_recorded_Game(update, context):
  user_data = context.user_data
  user_data['recorded'] = False

  update.message.reply_text(
    '`Please enter {} player name:`'.format(SEAT_NAME[0]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME

@catch_error
def set_game_venue(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  text = update.message.text
  venue_list = user_data['venue_list']

  check = list(filter(lambda h: h['name'] == text, venue_list))
  if len(check) == 0:

    reply_keyboard = [[h['name'] for h in venue_list[i:i+2]] for i in range(0, len(venue_list), 2)]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
    '`Invalid venue name inputted. Please select a valid venue name`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

    return SET_VENUE

  venue = check[0]
  user_data['venue'] = venue

  if DB_CONFIG['in_use']:
    mode_list = db.get_mode_by_vid(venue['vid'])
  elif SPREADSHEET_CONFIG['in_use']:
    mode_list = gfunc.filter_mode_by_bid(bot_data['mode_list'], venue['vid'])
  user_data['mode_list'] = mode_list

  reply_keyboard = [[h['name'] for h in mode_list[i:i+2]] for i in range(0, len(mode_list), 2)]
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
  mode_list = user_data['mode_list']

  check = list(filter(lambda h: h['name'] == text, mode_list))
  if len(check) == 0:
    reply_keyboard = [[h['name'] for h in mode_list[i:i+2]] for i in range(0, len(mode_list), 2)]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
    '`Invalid mode inputted. Please select a valid mode name`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

    return SET_MODE

  mode = check[0]
  user_data['mode'] = mode

  reply_keyboard = [['Confirm', 'Exit']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
  '`Venue: {}\nMode: {}\n\nIs this correct?`'.format(user_data['venue']['name'], user_data['mode']['name']),
  parse_mode=ParseMode.MARKDOWN_V2,
  reply_markup=markup)

  return CONFIRM_VENUE_MODE

@catch_error
def confirm_venue_mode(update, context):
  update.message.reply_text(
    '`Please enter {} player name or id number:`'.format(SEAT_NAME[0]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME

@catch_error
def exit_venue_mode(update, context):
  user_data = context.user_data

  update.message.reply_text("`Game settings have been discarded`", parse_mode=ParseMode.MARKDOWN_V2)
  user_data.clear()
  return ConversationHandler.END

@catch_error
def set_player_by_name(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  text = update.message.text
  name = func.handle_name(text)
  players = user_data['players']

  if name in BLOCKED_NAMES:
    update.message.reply_text("`This player name is not allowed`",
      parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME

  if user_data['recorded']:
    if DB_CONFIG['in_use']:
      player_info = db.get_player_by_name(name)
    elif SPREADSHEET_CONFIG['in_use']:
      player_info = gfunc.check_valid_name_from_list(name, bot_data['player_list'])

    if player_info is None:
      update.message.reply_text("`Please enter a valid name`", 
        parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME
  else:
    player_info = {'pid': 0, 'name': name, 'telegram_id': None}

  if player_info in players:
    update.message.reply_text("`This player has already been entered`",
    	parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME

  players.append(player_info)

  if len(players) < 4:
    update.message.reply_text("`Player Name {} entered\n"
                              "Please enter {} player's name`".format(func.get_player_name(player_info), SEAT_NAME[len(players)]),
                              parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME
  
  reply_keyboard = [['Proceed', 'Re-enter Names']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
  update.message.reply_text(
    "`East : {}\n"
    "South: {}\n"
    "West : {}\n"
    "North: {}\n\n"
    "Is this ok?`".
    format(func.get_player_name(players[0]), 
      func.get_player_name(players[1]), 
      func.get_player_name(players[2]), 
      func.get_player_name(players[3])),
		parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)
  return CONFIRM_PLAYER_NAME

@catch_error
def set_player_by_id(update, context):
  user_data = context.user_data
  bot_data = context.bot_data
  text = update.message.text
  players = user_data['players']

  if user_data['recorded']:
    if DB_CONFIG['in_use']:
      player_info = db.get_player_by_id(text)
    elif SPREADSHEET_CONFIG['in_use']:
      player_info = gfunc.check_valid_id_from_list(int(text), bot_data['player_list'])

    if player_info is None:
      update.message.reply_text("`Please enter a valid id`",
        parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME
  else:
    player_info = {'id': 0, 'name': func.handle_name(text), 'telegram_id': None}

  if player_info in players:
    update.message.reply_text("`This player has already been entered`",
    	parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME

  players.append(player_info)

  if len(players) < 4:
    update.message.reply_text("`Player Name {} entered\n"
                                "Please enter {} player's name`".format(func.get_player_name(player_info), SEAT_NAME[len(players)]),
    													parse_mode=ParseMode.MARKDOWN_V2)
    return SET_PLAYER_NAME
  
  reply_keyboard = [['Proceed', 'Re-enter Names']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
  update.message.reply_text(
    "`East : {}\n"
    "South: {}\n"
    "West : {}\n"
    "North: {}\n\n"
    "Is this ok?`".
    format(func.get_player_name(players[0]), 
      func.get_player_name(players[1]), 
      func.get_player_name(players[2]), 
      func.get_player_name(players[3])),
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)
  return CONFIRM_PLAYER_NAME

@catch_error
def confirm_player_name(update, context):
  user_data = context.user_data
  text = update.message.text

  if text == "Re-enter Names":
    user_data['players'] = []

    update.message.reply_text(
      '`Please enter {} player name or id number:`'.format(SEAT_NAME[0]),
      parse_mode=ParseMode.MARKDOWN_V2)

    return SET_PLAYER_NAME

  user_data['initial value'] = 250
  user_data['aka'] = 'Aka-Ari'
  user_data['uma'] = [15, 5, -5, -15]
  user_data['oka'] = 0
  user_data['chombo value'] = 40
  user_data['chombo option'] = 'Payment to all'
  user_data['kiriage'] = True
  user_data['atamahane'] = True

  return return_select_edit_settings(update, user_data)

def return_select_edit_settings(update, game):
  reply_keyboard = [['Done'], ['Kiriage Mangan', 'Multiple Ron'], ['Initial Value', 'Aka'], ['Uma', 'Oka'], ['Chombo Value', 'Chombo Options']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Which settings would you like to edit?\n\n`'
    + func.print_current_game_settings(game),
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_EDIT_SETTINGS

@catch_error
def select_edit_atamahane(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Is multiple ron allowed?:`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_ATAMAHANE

@catch_error
def set_atamahane(update, context):
  user_data = context.user_data
  text = update.message.text

  multiple_ron = text == 'Yes'
  user_data['atamahane'] = not multiple_ron

  return return_select_edit_settings(update, user_data)

@catch_error
def select_edit_kiriage_mangan(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Is there kiriage mangan?:`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_KIRIAGE

@catch_error
def set_kiriage_mangan(update, context):
  user_data = context.user_data
  text = update.message.text

  kiriage = text == 'Yes'
  user_data['kiriage'] = kiriage

  return return_select_edit_settings(update, user_data)

@catch_error
def select_edit_initial_value(update, context):
  reply_keyboard = [['250', '300']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Please select the initial value:`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_INITIAL_VALUE

@catch_error
def set_initial_value(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['initial value'] = int(text)

  return return_select_edit_settings(update, user_data)

@catch_error
def select_edit_aka(update, context):
  reply_keyboard = [['Aka-Ari', 'Aka-Nashi']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Please select the options for aka:`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_AKA

@catch_error
def set_aka(update, context):
  text = update.message.text
  user_data = context.user_data

  user_data['aka'] = text

  return return_select_edit_settings(update, user_data)

@catch_error
def select_edit_uma(update, context):
  reply_keyboard = [['15/5', '20/10'], ['Set custom uma']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Please select options for uma:`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_UMA

@catch_error
def set_default_uma(update, context):
  user_data = context.user_data
  text = update.message.text

  if text == "15/5":
  	user_data['uma'] = [15, 5, -5, -15]

  if text == "20/10":
  	user_data['uma'] = [20, 10, -10, -20]

  return return_select_edit_settings(update, user_data)

@catch_error
def select_custom_uma(update, context):
  user_data = context.user_data
  user_data['uma'] = []

  update.message.reply_text(
    '`Please enter uma for position 1`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_CUSTOM_UMA

@catch_error
def set_custom_uma(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['uma'].append(int(text))

  if len(user_data['uma']) < 4:
    update.message.reply_text("`Please enter uma for position {}`".format(len(user_data['uma']) + 1),
    													parse_mode=ParseMode.MARKDOWN_V2)
    return SET_CUSTOM_UMA

  return return_select_edit_settings(update, user_data)

@catch_error
def select_edit_oka(update, context):
  update.message.reply_text(
    '`Please enter oka amount`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_OKA

@catch_error
def select_edit_chombo_value(update, context):
  update.message.reply_text(
    '`Please enter amount of points to deduct when someone chombo\nNote that the value will not be split among other players.`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_CHOMBO_VALUE

@catch_error
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

@catch_error
def set_chombo_payment_option(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['chombo option'] = text

  return return_select_edit_settings(update, user_data)

@catch_error
def set_chombo_value(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['chombo value'] = int(text)

  return return_select_edit_settings(update, user_data)

@catch_error
def select_edit_done(update, context):
  user_data = context.user_data
  reply_keyboard = [['Start game', 'Discard game']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    func.print_game_settings_without_id(user_data)
    + '`\n\nIs the game settings ok?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return CONFIRM_GAME_SETTINGS

@catch_error
def set_oka(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['oka'] = int(text)

  return return_select_edit_settings(update, user_data)

def return_next_command(update, text):
  reply_keyboard = [['New Hand', 'End Game'], ['Delete Last Hand', 'Cancel Game']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_NEXT_COMMAND

@catch_error
def start_game(update, context):
  user_data = context.user_data

  player_names = func.get_all_player_name(user_data['players'])

  if user_data['result only']:
    user_data['final score'] = []
    update.message.reply_text(
      "`Please enter first player's final score in terms of 100.`",
      parse_mode=ParseMode.MARKDOWN_V2)

    return SET_PLAYER_SCORE

  if user_data['recorded'] and DB_CONFIG['in_use']:
    gid, start_date = db.set_new_game(user_data)
    user_data['id'] = gid
    user_data['date'] = start_date
  else:
    user_data['id'] = 0
    start_date = datetime.now()
    user_data['date'] = start_date.strftime("%d-%m-%Y")
    user_data['time'] = start_date.strftime('%H:%M:%S.%f')[:-4]
    user_data['datetime'] = start_date

  user_data['hands'] = []
  user_data['penalty'] = [0,0,0,0]

  return return_next_command(update, func.print_game_settings_info(user_data) +'\n'+ func.print_current_game_state(user_data['hands'], player_names, user_data['initial value']) + '`\n\nPlease select an option:`')

@catch_error
def set_player_score(update, context):
  user_data = context.user_data
  text = int(update.message.text)
  player_names = func.get_all_player_name(user_data['players'])

  score = user_data['final score']
  score.append(text)

  if len(score) < 4:
    update.message.reply_text(
      "`Please enter next player's final score in terms of 100.`",
      parse_mode=ParseMode.MARKDOWN_V2)

    return SET_PLAYER_SCORE

  text = "`Score:\n`"
  text += func.print_name_score(player_names, score)

  update.message.reply_text(
    "`Please enter value of riichi stick confiscated in terms of 100.`",
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_LEFTOVER_POOL

@catch_error
def set_leftover_pool(update, context):
  user_data = context.user_data
  text = int(update.message.text)
  player_names = func.get_all_player_name(user_data['players'])

  user_data['final pool'] = text

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Are there any penalties?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_HAVE_PENALTY

@catch_error
def discard_game_settings(update, context):
  user_data = context.user_data
  update.message.reply_text("`Game has been discarded.`",
    parse_mode=ParseMode.MARKDOWN_V2)

  user_data.clear()
  return ConversationHandler.END

@catch_error
def add_new_hand(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  user_data['new hand'] = func.create_new_hand(user_data['hands'], user_data['initial value'])
  user_data['multiple ron winner list'] = []
  user_data['multiple ron loser'] = None

  return return_4_player_done_option(update, player_names, SET_RIICHI,'`Who riichi?`')


def return_4_player_option(update, player_names, return_state, text):
  reply_keyboard = [
    ['{}'.format(player_names[0]), '{}'.format(player_names[1])],
    ['{}'.format(player_names[2]), '{}'.format(player_names[3])]
  ]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return return_state

def return_4_player_done_option(update, player_names, return_state, text):
  reply_keyboard = [
    ['{}'.format(player_names[0]), '{}'.format(player_names[1])],
    ['{}'.format(player_names[2]), '{}'.format(player_names[3])],
    ['Done']
  ]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return return_state

@catch_error
def set_hand_outcome(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']


  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  text = update.message.text

  new_hand['outcome'] = text

  if text == 'Mid Game Draw':
    reply_keyboard = [['Save', 'Discard']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
      func.print_hand_settings(new_hand, player_names)
      + '`\nIs this setting ok?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

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
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`How many Han?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_HAN

@catch_error
def set_winner(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  text = update.message.text

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_option(update, player_names, SET_WINNER, '`Invalid player name entered\nPlease enter a valid player name`')

  winner_idx = func.get_player_idx(text, player_names)

  if winner_idx in user_data['multiple ron winner list']:
    return return_4_player_option(update, player_names, SET_WINNER, '`This player have already been selected. Please select another player.`')

  if winner_idx == user_data['multiple ron loser']:
    return return_4_player_option(update, player_names, SET_WINNER, '`Invalid player name entered\nPlease enter a valid player name`')

  new_hand['winner idx'] = winner_idx
  user_data['multiple ron winner list'].append(winner_idx)

  if not user_data['multiple ron loser'] is None:
    new_hand['loser idx'] = user_data['multiple ron loser']
    return return_set_han(update)

  if new_hand['outcome'] == "Tsumo":
    return return_set_han(update)

  return return_4_player_option(update, player_names, SET_LOSER, '`Who dealt in?`')

@catch_error
def set_loser(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  text = update.message.text

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_option(update, player_names, SET_LOSER, '`Invalid player name entered\nPlease enter a valid player name`')

  loser_idx = func.get_player_idx(text, player_names)

  if loser_idx == new_hand['winner idx']:
    return return_4_player_option(update, player_names, SET_LOSER, '`Invalid Player Selected\nWho Lost?`')

  new_hand['loser idx'] = loser_idx
  user_data['multiple ron loser'] = loser_idx
  
  return return_set_han(update)

def return_set_fu(update, fu_list, text):
  reply_keyboard = [fu_list[i:i+3] for i in range(0, len(fu_list), 3)]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_FU

@catch_error
def set_han(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  text = update.message.text
  player_names = func.get_all_player_name(user_data['players'])

  new_hand['han'] = text

  if re.match('^[1-4]$', text):
    fu_list = func.get_valid_fu(new_hand['outcome'], new_hand['han'])
    return return_set_fu(update, fu_list, '`How many Fu?`')

  return return_save_discard_hand_option(update, new_hand, player_names)

@catch_error
def set_fu(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  text = update.message.text
  player_names = func.get_all_player_name(user_data['players'])

  fu_list = func.get_valid_fu(new_hand['outcome'], new_hand['han'])
  if not text in fu_list:
    return return_set_fu(update, fu_list, '`Invalid Fu Selected\nPlease choose a valid Fu`')

  new_hand['fu'] = text
  return return_save_discard_hand_option(update, new_hand, player_names)

@catch_error
def set_draw_tenpai(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  tenpai = new_hand['tenpai']
  text = update.message.text

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_done_option(update, player_names, SET_DRAW_TENPAI, '`Invalid player name entered\nPlease enter a valid player name`')

  player_idx = func.get_player_idx(text, player_names)

  tenpai[player_idx] = not tenpai[player_idx]

  return return_4_player_done_option(update, player_names, SET_DRAW_TENPAI, 
    '`Players who are in tenpai:\n-----------------------------\n`'
    + func.print_select_names(player_names, tenpai)
    + '`\nWho is in Tenpai?`')

@catch_error
def set_draw_tenpai_done(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  tenpai = new_hand['tenpai']

  return return_save_discard_hand_option(update, new_hand, player_names)

@catch_error
def set_riichi(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  riichi = new_hand['riichi']
  text = update.message.text

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_done_option(update, player_names, SET_RIICHI, '`Invalid player name entered\nPlease enter a valid player name`')

  player_idx = func.get_player_idx(text, player_names)

  riichi[player_idx] = not riichi[player_idx]

  return return_4_player_done_option(update, player_names, SET_RIICHI, 
    '`Players who riichi:\n-----------------------------\n`'
    + func.print_select_names(player_names, riichi)
    + '`\nWho riichi?`')

def return_save_discard_hand_option(update, new_hand, player_names):
  reply_keyboard = [['Save', 'Discard']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    func.print_hand_settings(new_hand, player_names)
    + '`\nIs this setting ok?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return PROCESS_HAND

@catch_error
def set_riichi_done(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])

  reply_keyboard = [['Tsumo', 'Ron'], ['Draw', 'Mid Game Draw'], ['Chombo']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`What is the hand outcome?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)
  return SET_HAND_OUTCOME

@catch_error
def set_chombo(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  chombo = new_hand['chombo']
  text = update.message.text

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_done_option(update, player_names, SET_CHOMBO, '`Invalid player name entered\nPlease enter a valid player name`')

  player_idx = func.get_player_idx(text, player_names)

  chombo[player_idx] = not chombo[player_idx]

  return return_4_player_done_option(update, player_names, SET_CHOMBO, 
    '`Players who Chombo:\n-----------------------------\n`'
    + func.print_select_names(player_names, chombo)
    + '`\nWho Chombo?`')

@catch_error
def set_chombo_done(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])

  reply_keyboard = [['Save', 'Discard']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    func.print_hand_settings(new_hand, player_names)
    + '`\nIs this setting ok?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return PROCESS_HAND

@catch_error
def discard_hand(update, context):
  user_data = context.user_data
  hands = user_data['hands']
  player_names = func.get_all_player_name(user_data['players'])
  hand_num = user_data['new hand']['hand num']

  while len(hands) > 0 and hands[-1]['hand num'] == hand_num:
    hands.pop()

  del user_data['new hand']

  return return_next_command(update, '`Hand have been discarded\n`' + func.print_current_game_state(hands, player_names, user_data['initial value']) +'`\n\nPlease select an option:`')

@catch_error
def save_hand(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])

  if new_hand['outcome'] == 'Chombo':
    func.process_chombo_hand(new_hand, user_data['chombo value'], user_data['chombo option'])
  else:
    func.process_hand(new_hand, user_data['kiriage'])

  if user_data['recorded'] and DB_CONFIG['in_use']:
    db.set_new_hand(new_hand, user_data['id'], func.get_all_player_id(user_data['players']))

  new_hand['winner idx list'] = user_data['multiple ron winner list']
  user_data['hands'].append(new_hand)
  del user_data['new hand']

  if SPREADSHEET_CONFIG['in_use'] and new_hand['outcome'] == 'Ron' and not user_data['atamahane'] and len(user_data['multiple ron winner list']) < 3:
    reply_keyboard = [['Yes', 'No']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
      '`Did anyone else Ron?`',
      parse_mode=ParseMode.MARKDOWN_V2,
      reply_markup=markup)

    return MULTIPLE_RON

  return return_next_command(update, 
    func.print_hand_title(new_hand)
    + func.print_score_change(user_data['hands'], player_names)
    + '`\n\nPlease select an option:`')

@catch_error
def confirm_multiple_ron(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  user_data['new hand'] = func.create_multiple_ron_hand(user_data['hands'])

  return return_4_player_option(update, player_names, SET_WINNER,'`Who Won?`')

@catch_error
def no_multiple_ron(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  new_hand = user_data['hands'][-1]
  return return_next_command(update, 
    func.print_hand_title(new_hand)
    + func.print_score_change(user_data['hands'], player_names)
    + '`\n\nPlease select an option:`')

@catch_error
def end_game(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`End Game?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return CONFIRM_GAME_END

@catch_error
def confirm_game_end(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Are there any penalties?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_HAVE_PENALTY

def return_to_next_command(update, context):
  user_data = context.user_data
  hands = user_data['hands']
  player_names = func.get_all_player_name(user_data['players'])

  return return_next_command(update, 
    func.print_current_game_state(hands, player_names, user_data['initial value'])
    + '`\n\nPlease select an option:`')

@catch_error
def select_have_penalty(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  penalty = user_data['penalty']

  return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, func.print_penalty(penalty, player_names) + '`Who has a penalty?`')

@catch_error
def set_penalty_player(update, context):
  user_data = context.user_data
  text = update.message.text
  penalty = user_data['penalty']
  player_names = func.get_all_player_name(user_data['players'])

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, '`Invalid player name entered\nPlease enter a valid player name`')

  player_idx = func.get_player_idx(text, player_names)

  user_data['chosen'] = player_idx

  update.message.reply_text(
    func.print_penalty(penalty, player_names)
    + '`Please enter the penalty amount for {} (without the negative sign)`'.format(player_names[player_idx]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PENALTY_VALUE

@catch_error
def set_penalty_value(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  penalty = user_data['penalty']
  text = update.message.text
  value = int(text)

  penalty[user_data['chosen']] = value
  del user_data['chosen']

  return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, func.print_penalty(penalty, player_names) + '`Who has a penalty?`')

@catch_error
def confirm_penalty_done(update, context):
  user_data = context.user_data
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Have you completed setting the penalty?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  if user_data['result only']:
    return CONFIRM_RESULT_ONLY

  return COMPLETE_GAME

@catch_error
def save_complete_game(update, context):
  user_data = context.user_data
  players = user_data['players']
  player_names = func.get_all_player_name(user_data['players'])

  if user_data['result only']:
    return confirm_result_only_game(update, context)

  func.process_game(user_data)

  if user_data['recorded']:
    if DB_CONFIG['in_use']:
      db.set_complete_game(user_data['id'], user_data['final score'], user_data['position'], user_data['penalty'])
      final_score_text = func.print_end_game_result(user_data['id'], player_names, user_data['final score'], user_data['position'], user_data['initial value'])
      update.message.reply_text("`Game has been completed.\n\n`" + final_score_text, parse_mode=ParseMode.MARKDOWN_V2)
      for player in players:
        if player['telegram_id']:
          push_msg.send_msg(func.print_game_confirmation(user_data['id'], final_score_text), player['telegram_id'])
    elif SPREADSHEET_CONFIG['in_use']:
      update.message.reply_text("`The game result is being submitted`", parse_mode=ParseMode.MARKDOWN_V2)
      user_data['duration'] = (datetime.now() - user_data['datetime']).total_seconds()
      gid = googlesheet.set_game_thread(update, user_data)

  user_data.clear()
  return ConversationHandler.END

@catch_error
def confirm_result_only_game(update, context):
  user_data = context.user_data
  players = user_data['players']
  player_names = func.get_all_player_name(players)

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    func.print_result_only_game_settings(user_data)
    + '`\n\nAre the game settings correct?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SAVE_RESULT_ONLY

@catch_error
def save_result_only_game(update, context):
  user_data = context.user_data
  players = user_data['players']
  player_names = func.get_all_player_name(user_data['players'])

  func.process_result_only(user_data)

  if user_data['recorded']:
    if DB_CONFIG['in_use']:
      gid = db.set_result_only_game(user_data)
    elif SPREADSHEET_CONFIG['in_use']:
      update.message.reply_text("`Game is currently being recorded please wait a moment.`", parse_mode=ParseMode.MARKDOWN_V2)
      gid = googlesheet.set_record_game(user_data)

  update.message.reply_text("`Game has been saved.`", parse_mode=ParseMode.MARKDOWN_V2)

  final_score_text = func.print_end_game_result(gid, player_names, user_data['final score'], user_data['position'], user_data['initial value'])

  for player in players:
    if not player['telegram_id'] is None:
      push_msg.send_msg(func.print_game_confirmation(gid, final_score_text), player['telegram_id'])

  user_data.clear()
  return ConversationHandler.END

@catch_error
def discard_result_only_game(update, context):
  update.message.reply_text("`Game settings have been discarded`", parse_mode=ParseMode.MARKDOWN_V2)
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

@catch_error
def delete_last_hand(update, context):
  user_data = context.user_data
  hands = user_data['hands']
  player_names = func.get_all_player_name(user_data['players'])
  text = update.message.text

  if len(hands) > 0 and text == 'Yes':
    last_hand_num = hands[-1]['hand num']
    if DB_CONFIG['in_use']:
      db.delete_last_hand(user_data['id'], last_hand_num)
    while len(hands) > 0 and hands[-1]['hand num'] == last_hand_num:
      hands.pop()

  return return_next_command(update, func.print_current_game_state(hands, player_names, user_data['initial value']) + '`\n\nPlease select an option:`')


@catch_error
def confirm_cancel_game(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Cancel Game?\nThe game's result will not be recorded.`",
    parse_mode=ParseMode.MARKDOWN_V2, 
    reply_markup=markup)

  return CANCEL_GAME

@catch_error
def quit(update, context):
  user_data = context.user_data

  if 'id' in user_data and user_data['id'] and DB_CONFIG['in_use']:
    db.quit_game(user_data['id'])

  update.message.reply_text("`User has exited successfully`", parse_mode=ParseMode.MARKDOWN_V2)
  user_data.clear()
  return ConversationHandler.END

@catch_error
def timeout(update, context):
  user_data = context.user_data

  if user_data['recorded']:
    func.process_game(user_data)
    if DB_CONFIG['in_use'] and 'id' in user_data and user_data['id']:
      players = user_data['players']
      player_names = func.get_all_player_name(user_data['players'])

      db.set_complete_game(user_data['id'], user_data['final score'], user_data['position'], user_data['penalty'], True)
      final_score_text = func.print_end_game_result(user_data['id'], player_names, user_data['final score'], user_data['position'], user_data['initial value'])

      update.message.reply_text("`Game have timeout and is assumed to be completed\n\n`" + final_score_text, parse_mode=ParseMode.MARKDOWN_V2)
      
      for player in players:
        if not player['telegram_id'] is None:
          push_msg.send_msg(func.print_game_confirmation(user_data['id'], final_score_text), player['telegram_id'])
    elif SPREADSHEET_CONFIG['in_use']:
      update.message.reply_text("`Game is currently being recorded please wait a moment.`", parse_mode=ParseMode.MARKDOWN_V2)
      gid = googlesheet.set_game_thread(update, user_data, True)

  else:
    update.message.reply_text("`User has timeout due to inactivity`", parse_mode=ParseMode.MARKDOWN_V2)

  user_data.clear()
  return ConversationHandler.END