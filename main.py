# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot
# https://python-telegram-bot.readthedocs.io/en/stable/index.html
# https://pypi.org/project/tinydb/
# https://pypi.org/project/python-crontab/

from telegram.ext import Updater, CommandHandler
from tinydb import TinyDB
from datetime import timedelta, datetime
from dateutil.parser import parse
from crontab import CronTab
import sys

#TODO:eliminare i reminder eventualmente
#TODO: aggiungere codici identificativi dei reminder (anche per poterli eliminare

# token fornito dal BotFather passato come argomento del comando di esecuzione del bot
TOKEN = str(sys.argv[1])
# user passato come parametro
USER = sys.argv[2]

# il bot programma l'invio dei messaggi con crontab
cron = CronTab(user=USER)

# il bot deve essere eseguito con docker, sarà contenuto nella cartella /botREMINDbot e il suo database in /database
db = TinyDB('/database/botREMINDbot_db.json')

# all'inizio dell'esecuzione ricontrolla il db e crea nuove

# estrae argomento dividendo la stringa in un array di parole, e levando il primo elemento della stringa (il comando)
def estrai_argomento(text):
    argument = text.split()
    argument.pop(0)
    return argument


# crea il comando partendo dai dati necessari per forwardMessage, da usare quando si crea il crontab
def crea_comando(token,message_id, from_chat_id, chat_id):
    return "curl -X POST -H 'Content-Type: application/json' -d '{\"chat_id\": \"" + str(
        chat_id) + "\",\"from_chat_id\": \"" + str(from_chat_id) + "\",\"message_id\": \"" + str(
        message_id) + "\"}' https://api.telegram.org/bot" + token + "/forwardMessage"


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


# resituisce vero se la stringa è un intero falso altrimenti
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# riceve come argomento una stringa, restituisce un oggetto datetime.datetime
# traduce in datetime.datetime espressioni come 3 min, 3 h, 3 d, 01/01/01, 17:10 oppure 01/01/01 10:15
# get_time deve essere usato direttamente nella creazione dei contab job e non nel salvataggio sul db
def get_time(argument):
    if len(argument) > 1:
        # se l'array argument contiene più di un argomento allora può essere sia timedelta che una data con sia giorno che ora oppure da errore
        if argument[1] == 'min' and is_int(argument[0]):
            data = datetime.now() + timedelta(minutes=int(argument[0]))
        elif argument[1] == 'h' and is_int(argument[0]):
            data = datetime.now() + timedelta(hours=int(argument[0]))
        elif argument[1] == 'd' and is_int(argument[0]):
            data = datetime.now() + timedelta(days=int(argument[0]))
        elif is_date(f'{argument[0]} {argument[1]}'):
            data = parse(f'{argument[0]} {argument[1]}')
        else:
            raise TypeError('Command argument was not written in a valid format')
    elif len(argument) == 1:
        # se l'array argument contiene un solo elemento deve essere per forza una data altrimenti da errore
        if is_date(argument[0]):
            data = parse(argument[0])
        else:
            raise TypeError('Command argument was not written in a valid format')
    else:
        # 0 argomenti non hanno senso
        raise TypeError('Command argument was not written in a valid format')

    return data


# remind di un messaggio in chat privata
# salva in database id del messaggio, id della chat, id dello User e data
# avverte in privato l'utente se il reminder è salvato con successo o meno
def remindme(update, context):
    argument = estrai_argomento(update.message.text)
    try:
        # aggiungere comando crontab
        data = get_time(argument)
        scheduled_message = cron.new(
            command=crea_comando(TOKEN,update.message.reply_to_message.message_id, update.message.reply_to_message.chat.id,
                                 update.message.from_user.id))
        scheduled_message.setall(data)
        cron.write()

        db.insert({'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.from_user.id,
                   'data': data.strftime("%m/%d/%Y %H:%M:%S")})
        print(str({'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.from_user.id,
                   'data': data.strftime("%m/%d/% %H:%M:%S")}))
        # manda un messaggio per notificare che il reminder è stato impostato con successo
        context.bot.deleteMessage(update.message.chat.id, update.message.message_id)
        context.bot.send_message(update.message.from_user.id, f'Reminder has been saved successfully for {data.strftime("%m/%d/%Y %H:%M:%S")}.')
    except TypeError:
        print('Format not valid')
        context.bot.deleteMessage(update.message.chat.id, update.message.message_id)
        context.bot.send_message(update.message.from_user.id, 'Reminder format was not correct use /help for more.')


# remind di un messaggio direttamente nel gruppo
# salva in database id del messaggio, id della chat di provenienza,id del gruppo e data
# avverte sul gruppo se il reminder è salvato con successo o meno
def remindingroup(update, context):
    argument = estrai_argomento(update.message.text)
    try:
        # aggiungere comando crontab
        data = get_time(argument)
        scheduled_message = cron.new(command=
            crea_comando(TOKEN,update.message.reply_to_message.message_id, update.message.reply_to_message.chat.id,
                         update.message.chat.id))
        scheduled_message.setall(data)
        cron.write()

        db.insert({'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.chat.id,
                   'data': data.strftime("%m/%d/%Y\ %H:%M:%S")})
        print(str({'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.chat.id,
                   'data': data.strftime("%m/%d/%Y %H:%M:%S")}))
        # manda un messaggio per notificare che il reminder è stato impostato con successo
        context.bot.send_message(update.message.chat.id, f'Reminder has been saved successfully for {data.strftime("%m/%d/%Y %H:%M:%S")}.')
    except TypeError:
        print('Format not valid')
        context.bot.send_message(update.message.chat.id, 'Reminder format was not correct use /help for more.')


def help(update, context):
    help_text='''Hi, this bot helps you setting up reminders.
To use it correctly you should add it in your group.

Available commands
There are two available commands:
- /remindme *date* - Use it replying to a message and the bot will forward it to you in your personal chat at the desired date or time, it will also delete the message containing your command to avoid creating useless spam.
- /remindingroup *date* - Use it replying to a message and the bot will forward it to the group at the desired date or time.

About command arguments
You can write the remind expiry in a lot of different ways:
- as a date e.g 03/01/2021 to set a reminder for the 1 of March
- as a time e.g. 5:00 pm to set a reminder for today at 5 pm
- with bot a date and a time e.g. 03/17/2021 22:38:53
- as a duration e.g 1 min or 1 h or 1 d to set a reminder for 1 minute from now, or for 1 hour from now, or tomorrow
- you can also try using a different syntax and see if the bot correctly understands you.'''
    context.bot.send_message(update.message.chat.id,help_text)

    ...


def main():
    upd = Updater(TOKEN, use_context=True)
    disp = upd.dispatcher

    disp.add_handler(CommandHandler("remindme", remindme))
    disp.add_handler(CommandHandler("remindingroup", remindingroup))
    disp.add_handler(CommandHandler("help", help))

    upd.start_polling()

    upd.idle()


if __name__ == '__main__':
    main()
