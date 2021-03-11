# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot
# https://python-telegram-bot.readthedocs.io/en/stable/index.html
# https://pypi.org/project/tinydb/
#https://pypi.org/project/python-crontab/

from telegram.ext import Updater, CommandHandler
from tinydb import TinyDB, Query
from datetime import timedelta,datetime
from dateutil.parser import parse
from crontab import CronTab
import sys

# token fornito dal BotFather passato come argomento del comando di esecuzione del bot
TOKEN = sys.argv[1]

# il bot deve essere eseguito con docker, sarà contenuto nella cartella /botREMINDbot e il suo database in /database
#db = TinyDB('/database/botREMINDbot_db.json')
# TODO: rimettere precedente percorso del database
db = TinyDB('/home/dav/PycharmProjects/botREMINDbot/database.json')

# all'inizio dell'esecuzione ricontrolla il db e crea nuove

# TODO: aggiungere touch /database/botREMINDbot_db.json al Dockerfile
# TODO: aggiornare crontab alla prima esecuzione del bot usando il database

# estrae argomento dividendo la stringa in un array di parole, e levando il primo elemento della stringa (il comando)
def estrai_argomento(text):
    argument=text.split()
    argument.pop(0)
    return argument

#crea il comando partendo dai dati necessari per forwardMessage, da usare quando si crea il crontab
def crea_comando(message_id,from_chat_id,chat_id) :
    return "curl -X POST -H 'Content-Type: application/json' -d '{\"chat_id\": \""+str(chat_id)+"\",\"from_chat_id\": \""+str(from_chat_id)+"\",\"message_id\": \""+str(message_id)+"\"}' https://api.telegram.org/bot"+TOKEN+"/forwardMessage"


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

#resituisce vero se la stringa è un intero falso altrimenti
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

#stabilisce se l'argomento è una data accettabile e si può salvare nel database
def is_ok(argument):
    if len(argument)>1:
        #se l'array argument contiene più di un argomento allora può essere sia timedelta che una data con sia giorno che ora oppure da errore
        if argument[1]== 'min' and is_int(argument[0]):
            return True
        elif argument[1]== 'h'and is_int(argument[0]):
            return True
        elif argument[1]== 'd'and is_int(argument[0]):
            return True
        elif is_date(f'{argument[0]} {argument[1]}'):
            return True
        else:
            return False
    elif len(argument)==1:
        #se l'array argument contiene un solo elemento deve essere per forza una data altrimenti da errore
        if is_date(argument[0]):
            return True
        else:
            return False
    else:
        #0 argomenti non hanno senso
        return False


# riceve come argomento una stringa, restituisce un oggetto datetime.timedelta o datetime.time
# traduce in datetime.timedelta espressioni come 3 min, 3 h, 3 d, tomorrow
# traduce in datetime.time espressioni come 01/01/01, 17:10 oppure 01/01/01 10:15
# gettime deve essere usato direttamente in JobQueue e non nel salvataggio sul db
def gettime(argument):
    print(str(argument))
    if len(argument)>1:
        #se l'array argument contiene più di un argomento allora può essere sia timedelta che una data con sia giorno che ora oppure da errore
        if argument[1]== 'min' and is_int(argument[0]):
            data=timedelta(minutes=argument[0])
        elif argument[1]== 'h'and is_int(argument[0]):
            data = timedelta(hours=argument[0])
        elif argument[1]== 'd'and is_int(argument[0]):
            data=timedelta(days=argument[0])
        elif is_date(f'{argument[0]} {argument[1]}'):
            data=parse(f'{argument[0]} {argument[1]}')
        else:
            raise Exception('Command argument was not written in a valid format')
    elif len(argument)==1:
        #se l'array argument contiene un solo elemento deve essere per forza una data altrimenti da errore
        if is_date(argument[0]):
            data = parse(argument[0])
        else:
            raise Exception('Command argument was not written in a valid format')
    else:
        raise Exception('Command argument was not written in a valid format')

    return data

# remind di un messaggio in chat privata
# salva in database id del messaggio, id della chat, id dello User e data
# avverte in privato l'utente se il reminder è salvato con successo o meno
def remindme(update, context):
    argument=estrai_argomento(update.message.text)
    if(is_ok(argument)):
        db.insert({'message_id': update.message.reply_to_message.message_id,'from_chat_id': update.message.reply_to_message.chat.id,'chat_id': update.message.from_user.id,'data': argument})
        print(str({'message_id': update.message.reply_to_message.message_id,'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.from_user.id,'data': argument}))
        #TODO: aggiungere comando crontab
        #manda un messaggio per notificare che il reminder è stato impostato con successo
        context.bot.send_message(update.message.from_user.id,'Reminder has been saved successfully')
    else:
        print('Format not valid')
        context.bot.send_message(update.message.from_user.id,'Reminder format was not correct use /help for more')

# remind di un messaggio direttamente nel gruppo
# salva in database id del messaggio, id della chat di provenienza,id del gruppo e data
# avverte sul gruppo se il reminder è salvato con successo o meno
def remindingroup(update, context):
    argument=estrai_argomento(update.message.text)
    if(is_ok(argument)):
        db.insert({'message_id': update.message.reply_to_message.message_id,'from_chat_id': update.message.reply_to_message.chat.id,'chat_id': update.message.chat.id,'data': argument})
        print(str({'message_id': update.message.reply_to_message.message_id,'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.chat.id,'data': argument}))
        # TODO: aggiungere comando crontab
        #manda un messaggio per notificare che il reminder è stato impostato con successo
        context.bot.send_message(update.message.chat.id,'Reminder has been saved successfully')
    else:
        print('Format not valid')
        context.bot.send_message(update.message.chat.id,'Reminder format was not correct use /help for more')


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
