# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot
# https://python-telegram-bot.readthedocs.io/en/stable/index.html
# https://pypi.org/project/tinydb/

from telegram.ext import Updater, CommandHandler
from tinydb import TinyDB, Query
import sys

# token fornito dal BotFather passato come argomento del comando di esecuzione del bot
TOKEN = sys.argv[1]

#il bot deve essere eseguito con docker, sarà contenuto nella cartella /botREMINDbot e il suo database in /database
db=TinyDB('/database/botREMINDbot_db.json')
# TODO: aggiungere touch /database/botREMINDbot_db.json al Dockerfile

#TODO: riceve comando remind sia da gruppi che da chat

# estrae argomento dividendo la stringa in un array di parole, poi prende il secondo elemento della stringa (il primo è il comando)
def estrai_argomento(text):
    return text.split()[1].strip()

#remind di un messaggio in chat privata
def remindme(update, context):
    #TODO: salva in database id del messaggio, id dello User e data
    ...
    #update.message.


# remind di un messaggio direttamente nel gruppo
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