import telegram
import os

def send_telegram_message(message):
    """
    Send a message to a Telegram bot.

    :param message: The message to send.
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id:
        bot = telegram.Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message)
    else:
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
