import helper_functions as func
from telegram import ReplyKeyboardMarkup, ParseMode
from log_helper import logger
import push_msg

def check_valid_name_from_list(name, player_list):
	filtered = list(filter(lambda x: x['name'] == name, player_list))
	return filtered[0] if len(filtered) else None

def check_valid_id_from_list(pid, player_list):
	filtered = list(filter(lambda x: x['pid'] == pid, player_list))
	return filtered[0] if len(filtered) else None

def filter_mode_by_bid(mode_list, vid):
	return list(filter(lambda x: x['vid'] == vid, mode_list))

def print_final_outcome(update, game, gid):
	players = game['players']
	player_names = func.get_all_player_name(players)

	final_score_text = func.print_end_game_result(gid, player_names, game['final score'], game['position'])

	update.message.reply_text("`Game have been completed.\n\n`" + final_score_text, parse_mode=ParseMode.MARKDOWN_V2)

	for player in players:
		if player['telegram_id']:
			try:
				push_msg.send_msg(func.print_game_confirmation(gid, final_score_text), player['telegram_id'])
			except:
				logger.error("Failed to send game confirmation to {}".format(player['telegram_id']))