# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot
# https://python-telegram-bot.readthedocs.io/en/stable/index.html

from telegram.ext import Updater, CommandHandler
import sys

# token fornito dal BotFather
TOKEN = sys.argv[1]

#TODO: riceve comando remind sia da gruppi che da chat

# estrae argomento dividendo la stringa in un array di parole, poi prende il secondo elemento della stringa (il primo è il comando)
def estrai_argomento(text):
    return text.split()[1].strip()


def remindme(update, context):
    #TODO: salva in database id del messaggio, id dello User e data
    ...
    #update.message.


# come si comporta quando riceve un messaggio di testo in un canale
def remindingroup(update, context):
    #TODO: salva in database id del messaggio, id del gruppo e data
    ...


def main():
    upd = Updater(TOKEN, use_context=True)
    disp = upd.dispatcher

    # ogni volta che si crea un comando che inizia con / bisogna aggiungere un handler come segue:
    disp.add_handler(CommandHandler("remindme", remindme))
    disp.add_handler(CommandHandler("remindingroup", remindingroup))

    upd.start_polling()

    upd.idle()

if __name__ == '__main__':
    main()