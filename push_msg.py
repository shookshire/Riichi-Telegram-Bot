from config import BOT_CONFIG
import telegram
from telegram import ParseMode

def send_msg(msg, chat_id, token=BOT_CONFIG['bot_token']):
	bot = telegram.Bot(token=token)
	bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN_V2)