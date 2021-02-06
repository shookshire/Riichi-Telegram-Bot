import logging
from logging.handlers import TimedRotatingFileHandler
from functools import wraps
from config import LOGGER_CONFIG

logname = "./logs/log_file.log"
handler = TimedRotatingFileHandler(logname, when="W0", interval=1)
handler.suffix = "%Y%m%d_%H%M%S"

logging_level = logging.INFO if LOGGER_CONFIG['level'] == 'INFO' else logging.WARNING

#Create and configure logger 
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', 
                    level=logging_level,
                    handlers=[handler])

#Creating an object 
logger=logging.getLogger('riichi_app_log') 

def catch_error(f):
  @wraps(f)
  def wrap(update, context):
    logger.debug("User {user} Sent {message}".format(user=update.message.chat.id, message=update.message.text))
    try:
      return f(update, context)
    except Exception as e:
      # Add info to error tracking
      logger.error(str(e))
      update.message.reply_text("An error occured ...\nPlease contact the admin ...")

  return wrap
