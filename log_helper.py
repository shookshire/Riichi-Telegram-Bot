import logging
from logging.handlers import TimedRotatingFileHandler
from functools import wraps

logname = "logs/log_file.log"
handler = TimedRotatingFileHandler(logname, when="M", interval=1)
handler.suffix = "%Y%m%d%H%M%S"

#Create and configure logger 
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', 
                    level=logging.WARNING,
                    handlers=[handler])

#Creating an object 
logger=logging.getLogger('riichi_app_log') 

def catch_error(f):
  @wraps(f)
  def wrap(update, context):
    logger.info("User {user} Sent {message}".format(user=update.message.chat.id, message=update.message.text))
    try:
      return f(update, context)
    except Exception as e:
      # Add info to error tracking
      logger.error(str(e))
      update.message.reply_text("An error occured ...\nPlease contact the admin ...")

  return wrap
