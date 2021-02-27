#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import re
import numpy as np
import string

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import handler
import mcr_handler
from config import BOT_CONFIG
from constants import *
from log_helper import logger

def main():
  # Create the Updater and pass it your bot's token.
  # Make sure to set use_context=True to use the new context based callbacks
  # Post version 12 this will no longer be necessary
  updater = Updater(BOT_CONFIG['bot_token'], use_context=True)

  # Get the dispatcher to register handlers
  dp = updater.dispatcher

  # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
  conv_handler = ConversationHandler(
    entry_points=[
      CommandHandler('help', handler.helper),
      CommandHandler('start', handler.helper),
      CommandHandler('riichi', handler.start_new_game),
      # CommandHandler('record', handler.start_input_game_result),
      CommandHandler('get_telegram_id', handler.get_telegram_id),
      CommandHandler('get_sgriichi_id', handler.get_sgriichi_id),
      CommandHandler('update', handler.get_googlesheet_data)
    ],

    states={
      SET_RECORDED_GAME: [
        MessageHandler(Filters.regex('^Yes$'), handler.set_recorded_game),
        MessageHandler(Filters.regex('^No$'), handler.set_not_recorded_Game)
      ],
      SET_VENUE: [
        MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Quit$')), handler.set_game_venue)
      ],
      SET_MODE: [
        MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Quit$')), handler.set_game_mode)
      ],
      CONFIRM_VENUE_MODE: [
        MessageHandler(Filters.regex('^Confirm$') & ~(Filters.command | Filters.regex('^Quit$')), handler.confirm_venue_mode),
        MessageHandler(Filters.regex('^Exit$') & ~(Filters.command | Filters.regex('^Quit$')), handler.exit_venue_mode)
      ],
      SET_PLAYER_NAME: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^Quit$')),
                       handler.set_player_by_name),
        MessageHandler(Filters.regex('^[0-9]+$'),
                       handler.set_player_by_id)
      ],
      CONFIRM_PLAYER_NAME: [
        MessageHandler(Filters.regex('^(Re-enter Names|Proceed)$'),
                        handler.confirm_player_name)
      ],
      SELECT_EDIT_SETTINGS: [
        MessageHandler(Filters.regex('^Initial Value$'),
                        handler.select_edit_initial_value),
        MessageHandler(Filters.regex('^Aka$'),
                        handler.select_edit_aka),
        MessageHandler(Filters.regex('^Uma$'),
                        handler.select_edit_uma),
        MessageHandler(Filters.regex('^Oka$'),
                        handler.select_edit_oka),
        MessageHandler(Filters.regex('^Chombo Value$'),
                        handler.select_edit_chombo_value),
        MessageHandler(Filters.regex('^Chombo Options$'),
                        handler.select_edit_chombo_payment_option),
        MessageHandler(Filters.regex('^Kiriage Mangan$'),
                        handler.select_edit_kiriage_mangan),
        MessageHandler(Filters.regex('^Multiple Ron$'),
                        handler.select_edit_atamahane),
        MessageHandler(Filters.regex('^Done$'),
                        handler.select_edit_done)
      ],
      SET_ATAMAHANE: [
        MessageHandler(Filters.regex('^(Yes|No)$'),
                                handler.set_atamahane)
      ],
      SET_KIRIAGE: [
        MessageHandler(Filters.regex('^(Yes|No)$'),
                                handler.set_kiriage_mangan)
      ],
      SET_INITIAL_VALUE: [
        MessageHandler(Filters.regex('^(250|300)$'),
                                handler.set_initial_value)
      ],
      SET_AKA: [
        MessageHandler(Filters.regex('^(Aka-Ari|Aka-Nashi)$'),
                                handler.set_aka)
      ],
      SET_UMA: [
        MessageHandler(Filters.regex('^(15/5|20/10)$'), handler.set_default_uma),
        MessageHandler(Filters.regex('^Set custom uma$'), handler.select_custom_uma)
      ],
      SET_CUSTOM_UMA: [
        MessageHandler(Filters.regex('^-?[0-9]+$'), handler.set_custom_uma)
      ],
      SET_OKA: [
        MessageHandler(Filters.regex('^[0-9]+$'),
                        handler.set_oka)
      ],
      SET_CHOMBO_VALUE: [
        MessageHandler(Filters.regex('^[0-9]+$'),
                        handler.set_chombo_value)
      ],
      SET_CHOMBO_PAYMENT_OPTION: [
        MessageHandler(Filters.regex('^(Payment to all|Flat deduction)$'),
                        handler.set_chombo_payment_option)
      ],
      CONFIRM_GAME_SETTINGS: [
        MessageHandler(Filters.regex('^Start game$'), handler.start_game),
        MessageHandler(Filters.regex('^Discard game$'), handler.discard_game_settings)
      ],
      SELECT_NEXT_COMMAND: [
        MessageHandler(Filters.regex('^New Hand$'), handler.add_new_hand),
        MessageHandler(Filters.regex('^End Game$'), handler.end_game),
        MessageHandler(Filters.regex('^Delete Last Hand$'), handler.confirm_delete_last_hand),
        MessageHandler(Filters.regex('^Cancel Game$'), handler.confirm_cancel_game)
      ],
      DELETE_LAST_HAND: [
        MessageHandler(Filters.regex('^(Yes|No)$'), handler.delete_last_hand)
      ],
      CANCEL_GAME: [
        MessageHandler(Filters.regex('^(Yes|No)$'), handler.quit)
      ],
      SET_HAND_OUTCOME: [
        MessageHandler(Filters.regex('^(Tsumo|Ron|Draw|Mid Game Draw|Chombo)$'), handler.set_hand_outcome)
      ],
      SET_WINNER: [
        MessageHandler(Filters.regex('^[a-zA-Z0-9 ]+$') & ~(Filters.command | Filters.regex('^(Quit)$')), handler.set_winner)
      ],
      SET_LOSER: [
        MessageHandler(Filters.regex('^[a-zA-Z0-9 ]+$') & ~(Filters.command | Filters.regex('^(Quit)$')), handler.set_loser)
      ],
      SET_DRAW_TENPAI: [
        MessageHandler(Filters.regex('^[a-zA-Z0-9 ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done|Mid Game Draw)$')), handler.set_draw_tenpai),
        MessageHandler(Filters.regex('^Done$'), handler.set_draw_tenpai_done)
      ],
      SET_HAN: [
        MessageHandler(Filters.regex('^([1-9]|1[0-3])$'), handler.set_han)
      ],
      SET_FU: [
        MessageHandler(Filters.regex('^(25|[2-9]0|1[0-3]0)$'), handler.set_fu)
      ],
      SET_RIICHI: [
        MessageHandler(Filters.regex('^[a-zA-Z0-9 ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_riichi),
        MessageHandler(Filters.regex('^Done$'), handler.set_riichi_done)
      ],
      SET_CHOMBO: [
        MessageHandler(Filters.regex('^[a-zA-Z0-9 ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_chombo),
        MessageHandler(Filters.regex('^Done$'), handler.set_chombo_done)
      ],
      PROCESS_HAND: [
        MessageHandler(Filters.regex('^Save$'), handler.save_hand),
        MessageHandler(Filters.regex('^Discard$'), handler.discard_hand)
      ],
      MULTIPLE_RON: [
        MessageHandler(Filters.regex('^Yes$'), handler.confirm_multiple_ron),
        MessageHandler(Filters.regex('^No$'), handler.no_multiple_ron)
      ],
      CONFIRM_GAME_END: [
        MessageHandler(Filters.regex('^Yes$'), handler.confirm_game_end),
        MessageHandler(Filters.regex('^No$'), handler.return_to_next_command)
      ],
      SELECT_HAVE_PENALTY: [
        MessageHandler(Filters.regex('^Yes$'), handler.select_have_penalty),
        MessageHandler(Filters.regex('^No$'), handler.save_complete_game)
      ],
      SET_PENALTY_PLAYER: [
        MessageHandler(Filters.regex('^[a-zA-Z0-9 ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_penalty_player),
        MessageHandler(Filters.regex('^Done$'), handler.confirm_penalty_done)
      ],
      SET_PENALTY_VALUE: [
        MessageHandler(Filters.regex('^[0-9]+$'), handler.set_penalty_value)
      ],
      COMPLETE_GAME: [
        MessageHandler(Filters.regex('^Yes$'), handler.save_complete_game),
        MessageHandler(Filters.regex('^No$'), handler.select_have_penalty)
      ],
      SET_PLAYER_SCORE: [
        MessageHandler(Filters.regex('^-?[0-9]+$'), handler.set_player_score)
      ],
      SET_LEFTOVER_POOL: [
        MessageHandler(Filters.regex('^[0-9]*0$'), handler.set_leftover_pool)
      ],
      CONFIRM_RESULT_ONLY: [
        MessageHandler(Filters.regex('^[0-9]+0$'), handler.set_leftover_pool)
      ],
      SAVE_RESULT_ONLY: [
        MessageHandler(Filters.regex('^Yes$'), handler.save_result_only_game),
        MessageHandler(Filters.regex('^No$'), handler.discard_result_only_game)
      ],
      ConversationHandler.TIMEOUT: [
        MessageHandler(Filters.text | Filters.command, handler.timeout)
      ]
    },

    fallbacks=[CommandHandler('quit', handler.quit)],
    conversation_timeout=BOT_CONFIG['timeout']
  )

  # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
  conv_handler_mcr = ConversationHandler(
    entry_points=[
      CommandHandler('mcr', mcr_handler.start_new_game),
    ],

    states={
      MCR_SET_PLAYER_NAME: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^Quit$')),
                       mcr_handler.set_player_by_name)
      ],
      MCR_CONFIRM_PLAYER_NAME: [
        MessageHandler(Filters.regex('^(Re-enter Names|Proceed)$') & ~(Filters.command | Filters.regex('^Quit$')),
                       mcr_handler.confirm_player_name)
      ],
      MCR_SELECT_NEXT_COMMAND: [
        MessageHandler(Filters.regex('^Draw$'), mcr_handler.set_draw_hand),
        MessageHandler(Filters.regex('^(Self Draw|Win Off Discard)$'), mcr_handler.set_win_hand),
        MessageHandler(Filters.regex('^(Delete Last Hand)$'), mcr_handler.delete_last_hand),
        MessageHandler(Filters.regex('^(End Game)$'), mcr_handler.confirm_end_game)
      ],
      MCR_SET_WINNING_PLAYER: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^Quit$')),
                       mcr_handler.set_winner)
      ],
      MCR_SET_DEAL_IN_PLAYER: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^Quit$')),
                       mcr_handler.set_loser)
      ],
      MCR_SET_HAND_VALUE: [
        MessageHandler(Filters.regex('^[0-9]+$'),
                        mcr_handler.set_hand_value)
      ],
      MCR_CONFIRM_GAME_END: [
        MessageHandler(Filters.regex('^(Yes|No)$'), mcr_handler.end_game)
      ],
    },

    fallbacks=[CommandHandler('quit', handler.quit)],
    conversation_timeout=BOT_CONFIG['timeout']
  )

  dp.add_handler(conv_handler)
  dp.add_handler(conv_handler_mcr, 1)

  # Start the Bot
  updater.start_polling()

  print('App has started running')
  logger.trace("App has started running")

  # Run the bot until you press Ctrl-C or the process receives SIGINT,
  # SIGTERM or SIGABRT. This should be used most of the time, since
  # start_polling() is non-blocking and will stop the bot gracefully.
  updater.idle()


if __name__ == '__main__':
  main()

"""
      
"""