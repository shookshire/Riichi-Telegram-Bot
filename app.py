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

import logging
import re
import numpy as np
import string

from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import handler
from config import BOT_CONFIG
from constants import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
  # Create the Updater and pass it your bot's token.
  # Make sure to set use_context=True to use the new context based callbacks
  # Post version 12 this will no longer be necessary
  updater = Updater(BOT_CONFIG['bot_token'], use_context=True)

  # Get the dispatcher to register handlers
  dp = updater.dispatcher

  # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
  conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', handler.start_new_game)],

    states={
      SET_PLAYER_NAME: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^Quit$')),
                       handler.set_player_by_name),
        MessageHandler(Filters.regex('^[0-9]+$'),
                       handler.set_player_by_id)
      ],
      CONFIRM_PLAYER_NAME: [
        MessageHandler(Filters.regex('^(Re-enter Names|Proceed to Aka settings)$'),
                        handler.confirm_player_name)
      ],
      SET_AKA: [
        MessageHandler(Filters.regex('^(Aka-Ari|Aka-Nashi)$'),
                                handler.set_aka)
      ],
      SET_UMA: [
        MessageHandler(Filters.regex('^(15/5|20/10)$'),
                        handler.set_default_uma),
        MessageHandler(Filters.regex('^Set custom uma$'),
                        handler.select_custom_uma)
      ],
      SET_CUSTOM_UMA: [
        MessageHandler(Filters.regex('^-?[0-9]+$'),
                        handler.set_custom_uma)
      ],
      SELECT_HAVE_OKA: [
        MessageHandler(Filters.regex('^(Yes|No)$'),
                        handler.select_have_oka)
      ],
      SET_OKA: [
        MessageHandler(Filters.regex('^[0-9]+$'),
                        handler.set_oka)
      ],
      CONFIRM_GAME_SETTINGS: [
        MessageHandler(Filters.regex('^Start game$'),
            handler.start_game),
        MessageHandler(Filters.regex('^Discard game$'),
            handler.discard_game_settings)
      ],
      SELECT_NEXT_COMMAND: [
        MessageHandler(Filters.regex('^New Hand$'), handler.add_new_hand),
        MessageHandler(Filters.regex('^End Game$'), handler.end_game),
        MessageHandler(Filters.regex('^Delete Last Hand$'), handler.delete_last_hand)
      ],
      SET_HAND_OUTCOME: [
        MessageHandler(Filters.regex('^(Tsumo|Ron|Draw|Chombo)$'), handler.set_hand_outcome)
      ],
      SET_WINNER: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^(Quit)$')), handler.set_winner)
      ],
      SET_LOSER: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^(Quit)$')), handler.set_loser)
      ],
      SET_DRAW_TENPAI: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_draw_tenpai),
        MessageHandler(Filters.regex('^Done$'), handler.set_draw_tenpai_done)
      ],
      SET_HAN: [
        MessageHandler(Filters.regex('^([1-9]|1[0-3])$'), handler.set_han)
      ],
      SET_FU: [
        MessageHandler(Filters.regex('^(25|[2-9]0|1[1-3]0)$'), handler.set_fu)
      ],
      SET_RIICHI: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_riichi),
        MessageHandler(Filters.regex('^Done$'), handler.set_riichi_done)
      ],
      SET_CHOMBO: [
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_chombo),
        MessageHandler(Filters.regex('^Done$'), handler.set_chombo_done)
      ],
      PROCESS_HAND: [
        MessageHandler(Filters.regex('^Save$'), handler.save_hand),
        MessageHandler(Filters.regex('^Discard$'), handler.discard_hand)
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
        MessageHandler(Filters.regex('^[a-zA-Z ]+$') & ~(Filters.command | Filters.regex('^(Quit|Done)$')), handler.set_penalty_player),
        MessageHandler(Filters.regex('^Done$'), handler.confirm_penalty_done)
      ],
      SET_PENALTY_VALUE: [
        MessageHandler(Filters.regex('^[0-9]+$'), handler.set_penalty_value)
      ],
      COMPLETE_GAME: [
        MessageHandler(Filters.regex('^Yes$'), handler.save_complete_game),
        MessageHandler(Filters.regex('^No$'), handler.select_have_penalty)
      ]
    },

    fallbacks=[]
  )

  dp.add_handler(conv_handler)

  # Start the Bot
  updater.start_polling()

  # Run the bot until you press Ctrl-C or the process receives SIGINT,
  # SIGTERM or SIGABRT. This should be used most of the time, since
  # start_polling() is non-blocking and will stop the bot gracefully.
  updater.idle()


if __name__ == '__main__':
  main()

"""
      
"""