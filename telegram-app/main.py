import handlers

import logging as log
import sys, locale
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

def main():
    # Set localization
    locale.setlocale(locale.LC_ALL, 'es_ES')

    # Init and config logger
    log.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=log.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Init bot
    TOKEN = open('/etc/telegram-bot-token/telegram-bot-token', 'r').read().strip()
    bot = Application.builder().token(TOKEN).build()

    # Init input handlers
    bot.add_handler(CommandHandler("start", handlers.start))
    bot.add_handler(CallbackQueryHandler(handlers.InlineKeyboardHandler))
    bot.add_handler(MessageHandler(filters.TEXT, handlers.text_input_handler))
    bot.add_handler(MessageHandler(filters.LOCATION, handlers.location_input_handler))

    bot.run_polling()

if __name__ == '__main__':
    main()
