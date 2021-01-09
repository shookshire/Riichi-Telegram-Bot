
from log_helper import catch_error
import helper_functions as func
import mcr_helper_functions as mcr_func


from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

from constants import *

@catch_error
def start_new_game(update, context):
  user_data = context.user_data
  user_data['players'] = []

  update.message.reply_text(
    '`Please enter {} player name:`'.format(SEAT_NAME[0]),
    parse_mode=ParseMode.MARKDOWN_V2)

  return MCR_SET_PLAYER_NAME

@catch_error
def set_player_by_name(update, context):
  user_data = context.user_data
  text = update.message.text
  name = func.handle_name(text)
  players = user_data['players']

  player_info = { 'name': name }

  if player_info in players:
    update.message.reply_text("`This player has already been entered`",
    	parse_mode=ParseMode.MARKDOWN_V2)
    return MCR_SET_PLAYER_NAME

  players.append(player_info)

  if len(players) < 4:
    update.message.reply_text("`Player Name {} entered\n"
                              "Please enter {} player's name`".format(func.get_player_name(player_info), SEAT_NAME[len(players)]),
                              parse_mode=ParseMode.MARKDOWN_V2)
    return MCR_SET_PLAYER_NAME
  
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
  return MCR_CONFIRM_PLAYER_NAME


def return_next_command(update, text):
  reply_keyboard = [['Tsumo', 'Ron', 'Draw'], ['Delete Last Hand', 'End Game']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return MCR_SELECT_NEXT_COMMAND 

@catch_error
def confirm_player_name(update, context):
  user_data = context.user_data
  text = update.message.text

  if text == "Re-enter Names":
    user_data['players'] = []

    update.message.reply_text(
      '`Please enter {} player name:`'.format(SEAT_NAME[0]),
      parse_mode=ParseMode.MARKDOWN_V2)

    return MCR_SET_PLAYER_NAME

  user_data['hands'] = []
  mcr_func.generate_new_hand(user_data['hands'], user_data['players'])

  return return_next_command(update, mcr_func.print_current_game_state(user_data['hands']))

@catch_error
def delete_last_hand(update, context):
	user_data = context.user_data

	hands = user_data['hands']
	hands.pop()
	if len(hands) > 0:
		hands.pop()

	mcr_func.generate_new_hand(hands, user_data['players'])
	return return_next_command(update, mcr_func.print_current_game_state(user_data['hands']))

@catch_error
def confirm_end_game(update, context):
  reply_keyboard = [['Yes', 'No']]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    '`End Game?`',
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return MCR_CONFIRM_GAME_END

@catch_error
def end_game(update, context):
	user_data = context.user_data
	text = update.message.text

	if text == 'No':
		return return_next_command(update, mcr_func.print_current_game_state(user_data['hands']))

	hand = user_data['hands'][-1]
	update.message.reply_text(
		'`The game has ended. Final score:\n\n`' +
		mcr_func.print_score(hand['final score']),
		parse_mode=ParseMode.MARKDOWN_V2)
	return ConversationHandler.END

@catch_error
def set_draw_hand(update, context):
  user_data = context.user_data

  have_next_hand = mcr_func.have_next_hand(user_data['hands'])
  if not have_next_hand:
  	hand = user_data['hands'][-1]
  	update.message.reply_text(
  		'`The game has ended. Final score:\n\n`' +
  		mcr_func.print_score(hand['final score']),
  		parse_mode=ParseMode.MARKDOWN_V2)
  	return ConversationHandler.END

  mcr_func.generate_new_hand(user_data['hands'], user_data['players'])

  return return_next_command(update, mcr_func.print_current_game_state(user_data['hands']))

def return_4_player_option(update, score, return_state, text):
  reply_keyboard = [
    ['{}'.format(score[0]['name']), '{}'.format(score[1]['name'])],
    ['{}'.format(score[2]['name']), '{}'.format(score[3]['name'])]
  ]
  markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

  update.message.reply_text(
    text,
    parse_mode=ParseMode.MARKDOWN_V2,
    reply_markup=markup)

  return return_state

@catch_error
def set_win_hand(update, context):
  user_data = context.user_data
  text = update.message.text

  hand = user_data['hands'][-1]
  hand['outcome'] = text

  return return_4_player_option(update, hand['initial score'], MCR_SET_WINNING_PLAYER, '`Who won?`')


@catch_error
def set_winner(update, context):
  user_data = context.user_data
  text = update.message.text
  name = func.handle_name(text)
  hand = user_data['hands'][-1]

  player_info = { 'name': name }

  if not {'name': name } in user_data['players']:
  	return return_4_player_option(update, hand['initial score'], MCR_SET_WINNING_PLAYER, '`Please enter a valid player name.`')

  hand['winner'] = name

  if hand['outcome'] == 'Ron':
  	return return_4_player_option(update, hand['initial score'], MCR_SET_DEAL_IN_PLAYER, '`Who deal in?`')

  update.message.reply_text(
    '`What is the hand value?`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return MCR_SET_HAND_VALUE

@catch_error
def set_loser(update, context):
  user_data = context.user_data
  text = update.message.text
  name = func.handle_name(text)
  hand = user_data['hands'][-1]

  player_info = { 'name': name }

  if not {'name': name } in user_data['players']:
  	return return_4_player_option(update, hand['initial score'], MCR_SET_DEAL_IN_PLAYER, '`Please enter a valid player name.`')

  if name == hand['winner']:
  	return return_4_player_option(update, hand['initial score'], MCR_SET_DEAL_IN_PLAYER, '`Please enter a valid player name.`')

  hand['loser'] = name

  update.message.reply_text(
    '`What is the hand value?`',
    parse_mode=ParseMode.MARKDOWN_V2)

  return MCR_SET_HAND_VALUE

@catch_error
def set_hand_value(update, context):
  user_data = context.user_data
  text = update.message.text
  score_value = int(text)
  hand = user_data['hands'][-1]

  mcr_func.process_hand(hand, score_value)
  have_next_hand = mcr_func.have_next_hand(user_data['hands'])
  if not have_next_hand:
  	update.message.reply_text(
  		'`The game has ended. Final score:\n\n`' +
  		mcr_func.print_score(hand['final score']),
  		parse_mode=ParseMode.MARKDOWN_V2)
  	return ConversationHandler.END

  mcr_func.generate_new_hand(user_data['hands'])
  return return_next_command(update, mcr_func.print_current_game_state(user_data['hands']))

