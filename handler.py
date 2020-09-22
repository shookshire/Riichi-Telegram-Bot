import logging
import re
import numpy as np
import string

from datetime import datetime
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import push_msg
import helper_functions as func
import db
from constants import *

def helper(update, context):

  update.message.reply_text(
    "/start : Start a new riichi score tracker. Game data for recorded games will be automatically stored to SMCRM server.\n/record : Save final game score to SMCRM server")

  return ConversationHandler.END

def start_new_game(update, context):
  user_data = context.user_data
  user_data['result only'] = False
  user_data['players'] = []

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Please select if this game will be recorded by SMCRM:\nDo note that only games played by 4 registered SMCRM players can be recorded`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_RECORDED_GAME

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


def set_recorded_game(update, context):
  user_data = context.user_data
  user_data['recorded'] = True

  update.message.reply_text(
    '`Please enter {} player name or id number:`'.format(SEAT_NAME[0]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME

def set_not_recorded_Game(update, context):
  user_data = context.user_data
  user_data['recorded'] = False

  update.message.reply_text(
    '`Please enter {} player name:`'.format(SEAT_NAME[0]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_PLAYER_NAME

def set_player_by_name(update, context):
  user_data = context.user_data
  text = update.message.text
  name = func.handle_name(text)
  players = user_data['players']

  if user_data['recorded']:
    player_info = db.get_player_by_name(name)
    if player_info is None:
      update.message.reply_text("`Please enter a valid name`", 
        parse_mode=ParseMode.MARKDOWN_V2)
      return SET_PLAYER_NAME
  else:
    player_info = {'id': 0, 'name': name, 'telegram_id': None}

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
  
  reply_keyboard = [['Re-enter Names', 'Proceed']]
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

def set_player_by_id(update, context):
  user_data = context.user_data
  text = update.message.text
  players = user_data['players']

  if user_data['recorded']:
    player_info = db.get_player_by_id(text)
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
  
  reply_keyboard = [['Re-enter Names', 'Proceed']]
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

  return return_select_edit_settings(update, user_data)

def return_select_edit_settings(update, game):
  reply_keyboard = [['Initial Value', 'Aka'], ['Uma', 'Oka'], ['Chombo Value', 'Chombo Options'], ['Done']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Which settings would you like to edit?\n\n`'
    + func.print_current_game_settings(game),
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_EDIT_SETTINGS

def select_edit_initial_value(update, context):
  reply_keyboard = [['250', '300']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Please select the initial value:`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_INITIAL_VALUE

def set_initial_value(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['initial value'] = int(text)

  return return_select_edit_settings(update, user_data)

def select_edit_aka(update, context):
  reply_keyboard = [['Aka-Ari', 'Aka-Nashi']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    "`Please select the options for aka:`",
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_AKA

def set_aka(update, context):
  text = update.message.text
  user_data = context.user_data

  user_data['aka'] = text

  return return_select_edit_settings(update, user_data)

def select_edit_uma(update, context):
  reply_keyboard = [['15/5', '20/10'], ['Set custom uma']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Please select options for oka:`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_UMA

def set_default_uma(update, context):
  user_data = context.user_data
  text = update.message.text

  if text == "15/5":
  	user_data['uma'] = [15, 5, -5, -15]

  if text == "20/10":
  	user_data['uma'] = [20, 10, -10, -20]

  return return_select_edit_settings(update, user_data)

def select_custom_uma(update, context):
  user_data = context.user_data
  user_data['uma'] = []

  update.message.reply_text(
    '`Please enter uma for position 1`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_CUSTOM_UMA

def set_custom_uma(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['uma'].append(int(text))

  if len(user_data['uma']) < 4:
    update.message.reply_text("`Please enter uma for position {}`".format(len(user_data['uma']) + 1),
    													parse_mode=ParseMode.MARKDOWN_V2)
    return SET_CUSTOM_UMA

  return return_select_edit_settings(update, user_data)

def select_edit_oka(update, context):
  update.message.reply_text(
    '`Please enter oka amount`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_OKA

def select_edit_chombo_value(update, context):
  update.message.reply_text(
    '`Please enter amount of points to deduct when someone chombo\nNote that the value will not be split among other players.`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return SET_CHOMBO_VALUE

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

def set_chombo_payment_option(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['chombo option'] = text

  return return_select_edit_settings(update, user_data)

def set_chombo_value(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['chombo value'] = int(text)

  return return_select_edit_settings(update, user_data)

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

def set_oka(update, context):
  user_data = context.user_data
  text = update.message.text

  user_data['oka'] = int(text)

  return return_select_edit_settings(update, user_data)

def return_next_command(update, text):
  reply_keyboard = [['New Hand', 'End Game'], ['Delete Last Hand']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_NEXT_COMMAND

def start_game(update, context):
  user_data = context.user_data

  player_names = func.get_all_player_name(user_data['players'])

  if user_data['result only']:
    user_data['final score'] = []
    update.message.reply_text(
      "`Please enter first player's final score in terms of 100.`",
      parse_mode=ParseMode.MARKDOWN_V2)

    return SET_PLAYER_SCORE

  if user_data['recorded']:
    gid, start_date = db.set_new_game(user_data)
    user_data['id'] = gid
    user_data['date'] = start_date
  else:
    user_data['id'] = 0
    user_data['date'] = datetime.now().strftime("%d-%m-%Y")

  user_data['hands'] = []
  user_data['penalty'] = [0,0,0,0]

  return return_next_command(update, func.print_game_settings_info(user_data) +'\n'+ func.print_current_game_state(user_data['hands'], player_names, user_data['initial value']) + '`\n\nPlease select an option:`')

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

def set_leftover_pool(update, context):
  user_data = context.user_data
  text = int(update.message.text)
  player_names = func.get_all_player_name(user_data['players'])

  user_data['final pool'] = text

  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Are they any penalty?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SELECT_HAVE_PENALTY

def discard_game_settings(update, context):
  user_data = context.user_data
  update.message.reply_text("`Game have been discarded.`",
    parse_mode=ParseMode.MARKDOWN_V2)

  user_data.clear()
  return ConversationHandler.END

def add_new_hand(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  user_data['new hand'] = func.create_new_hand(user_data['hands'], user_data['initial value'])

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

def set_hand_outcome(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']


  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  text = update.message.text

  new_hand['outcome'] = text
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

def set_winner(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  text = update.message.text

  if not func.is_valid_player_name(text, player_names):
    return return_4_player_option(update, player_names, SET_WINNER, '`Invalid player name entered\nPlease enter a valid player name`')

  new_hand['winner idx'] = func.get_player_idx(text, player_names)

  if new_hand['outcome'] == "Tsumo":
    return return_set_han(update)

  return return_4_player_option(update, player_names, SET_LOSER, '`Who dealt in?`')

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
  
  return return_set_han(update)

def return_set_fu(update, fu_list, text):
  reply_keyboard = [fu_list[i:i+3] for i in range(0, len(fu_list), 3)]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return SET_FU

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
    '`Players who are in tenpai:\n---------------------------------------\n`'
    + func.print_select_names(player_names, tenpai)
    + '`\nWho is in Tenpai?`')

def set_draw_tenpai_done(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])
  tenpai = new_hand['tenpai']

  return return_save_discard_hand_option(update, new_hand, player_names)

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
    '`Players who riichi:\n---------------------------------------\n`'
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

def set_riichi_done(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])

  reply_keyboard = [['Tsumo', 'Ron'], ['Draw', 'Chombo']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`What is the hand outcome?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)
  return SET_HAND_OUTCOME

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
    '`Players who Chombo:\n---------------------------------------\n`'
    + func.print_select_names(player_names, chombo)
    + '`\nWho Chombo?`')

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

def discard_hand(update, context):
  user_data = context.user_data
  hands = user_data['hands']
  player_names = func.get_all_player_name(user_data['players'])
  del user_data['new hand']

  return return_next_command(update, '`Hand have been discarded\n\n`' + func.print_current_game_state(hands, player_names, user_data['initial value']) +'`Please select an option:`')

def save_hand(update, context):
  user_data = context.user_data
  new_hand = user_data['new hand']
  player_names = func.get_all_player_name(user_data['players'])

  if new_hand['outcome'] == 'Chombo':
    func.process_chombo_hand(new_hand, user_data['chombo value'], user_data['chombo option'])
  else:
    func.process_hand(new_hand)

  if user_data['recorded']:
    db.set_new_hand(new_hand, user_data['id'], func.get_all_player_id(user_data['players']))

  user_data['hands'].append(new_hand)
  del user_data['new hand']

  return return_next_command(update, 
    func.print_hand_settings(new_hand, player_names)
    + '`\n`' + func.print_score_change(new_hand, player_names)
    + '`\n\nPlease select an option:`')

def end_game(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`End Game?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return CONFIRM_GAME_END

def confirm_game_end(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`Are they any penalty?`',
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

def select_have_penalty(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  penalty = user_data['penalty']

  return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, func.print_penalty(penalty, player_names) + '`Who has a penalty?`')

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

def set_penalty_value(update, context):
  user_data = context.user_data
  player_names = func.get_all_player_name(user_data['players'])
  penalty = user_data['penalty']
  text = update.message.text
  value = int(text)

  penalty[user_data['chosen']] = value
  del user_data['chosen']

  return return_4_player_done_option(update, player_names, SET_PENALTY_PLAYER, func.print_penalty(penalty, player_names) + '`Who has a penalty?`')

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

def save_complete_game(update, context):
  user_data = context.user_data
  players = user_data['players']
  player_names = func.get_all_player_name(user_data['players'])

  if user_data['result only']:
    return confirm_result_only_game(update, context)

  func.process_game(user_data)

  if user_data['recorded']:
    db.set_complete_game(user_data['id'], user_data['final score'], user_data['position'], user_data['penalty'])

  final_score_text = func.print_end_game_result(user_data['id'], player_names, user_data['final score'], user_data['position'])

  update.message.reply_text("`Game have been completed.\n\n`" + final_score_text, parse_mode=ParseMode.MARKDOWN_V2)
  
  for player in players:
    if not player['telegram_id'] is None:
      push_msg.send_msg(func.print_game_confirmation(user_data['id'], player_names), player['telegram_id'])

  user_data.clear()
  return ConversationHandler.END

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

def save_result_only_game(update, context):
  user_data = context.user_data
  players = user_data['players']
  player_names = func.get_all_player_name(user_data['players'])

  gid = db.set_result_only_game(user_data)

  update.message.reply_text("`Game have been saved.`", parse_mode=ParseMode.MARKDOWN_V2)

  for player in players:
    if not player['telegram_id'] is None:
      push_msg.send_msg(func.print_game_confirmation(gid, player_names), player['telegram_id'])

  user_data.clear()
  return ConversationHandler.END

def discard_result_only_game(update, context):
  update.message.reply_text("`Game settings have been discarded`", parse_mode=ParseMode.MARKDOWN_V2)
  user_data.clear()
  return ConversationHandler.END

def delete_last_hand(update, context):
  user_data = context.user_data
  hands = user_data['hands']
  player_names = func.get_all_player_name(user_data['players'])

  if len(hands) > 0:
    last_hand_num = hands[-1]['hand num']
    db.delete_last_hand(user_data['id'], last_hand_num)
    hands.pop()

  return return_next_command(update, func.print_current_game_state(hands, player_names, user_data['initial value']) + '`\n\nPlease select an option:`')
