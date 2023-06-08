import logging as log
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

def main():
    import handlers
    
    #Init bot
    TOKEN = open('/etc/telegram-bot-token/telegram-bot-token', 'r').read().strip()
    bot = Application.builder().token(TOKEN).build()

    # Init input handlers
    bot.add_handler(CommandHandler("start", handlers.start))
    bot.add_handler(CallbackQueryHandler(handlers.InlineKeyboardHandler))
    bot.add_handler(MessageHandler(filters.TEXT, handlers.text_input_handler))
    bot.add_handler(MessageHandler(filters.LOCATION, handlers.location_input_handler))

    bot.run_polling()

if __name__ == '__main__':
    
    # Init and config logger
    log.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=log.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    main()
