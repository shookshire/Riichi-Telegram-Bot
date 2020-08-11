from config import BOT_CONFIG
import telegram

def send_msg(msg, chat_id, token=BOT_CONFIG['bot_token']):
	bot = telegram.Bot(token=token)
	bot.sendMessage(chat_id=chat_id, text=msg)