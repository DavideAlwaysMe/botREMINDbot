# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot
# https://python-telegram-bot.readthedocs.io/en/stable/index.html
# https://pypi.org/project/tinydb/
# https://pypi.org/project/python-crontab/
import pytz
from telegram.ext import Updater, CommandHandler
from tinydb import TinyDB, Query
from datetime import timedelta, datetime, timezone
from dateutil.parser import parse
from crontab import CronTab
import sys
from reminder_remove import remove
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

# TODO: comando /removereminder (deve eliminare reminder da crontab, delete reminder da crontab
#       e il messaggio dal database)
# TODO: fuso orario
# TODO: comando /privacy
# TODO: funzione get_timezone per cercare il fuso orario nel database timezone_db
# TODO: usare questo nell'impostare il promemoria: timezone_utc=pytz.timezone(timezone_name)        fatto ma non provato
# TODO: aggiungere al comando /help sia /removereminder che info su /timezone

# token fornito dal BotFather passato come argomento del comando di esecuzione del bot
TOKEN = str(sys.argv[1])
# user passato come parametro
USER = sys.argv[2]

# il bot programma l'invio dei messaggi con crontab
cron = CronTab(user=USER)

# il bot deve essere eseguito con docker, sarà contenuto nella cartella /botREMINDbot e il suo database in /database
db = TinyDB('/database/botREMINDbot_db.json')
timezone_db = TinyDB('/database/timezone_db.json')


# all'inizio dell'esecuzione ricontrolla il db e crea nuove

# estrae argomento dividendo la stringa in un array di parole, e levando il primo elemento della stringa (il comando)
def estrai_argomento(text):
    argument = text.split()
    argument.pop(0)
    return argument


# crea il comando partendo dai dati necessari per forwardMessage, da usare quando si crea il crontab
def crea_comando(token, message_id, from_chat_id, chat_id):
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


# itera nel database e restituisce il primo numero intero libero
def generate_id():
    lista_messaggi = db.all()
    job_id = 0
    found_id = False
    while not found_id:
        found_id = True
        job_id += 1
        # itera nei messaggi programmati, se l'id è già in uso esce e ricomincia il ciclo
        for messaggio in lista_messaggi:
            if messaggio['job_id'] == str(job_id):
                found_id = False
                break

    return job_id


# funzione che riceve come parametro l'id della chat e controlla nel database timezone se ci sono info sul quella chat,
# restituisce il nome come stringa di un fuso orario se presenti info, altrimenti UTC
def get_timezone(chat_id):
    timezone_list = timezone_db.all()
    # itera tra gli elementi del database e controlla se esiste già una preferenza per quella chat
    for chat_tz in timezone_list:
        if chat_tz['chat_id'] == chat_id:
            return chat_tz['timezone']
    # se non ha trovato nessuna preferenza restituisce utc
    return 'UTC'


def has_timezone(chat_id):
    timezone_list = timezone_db.all()
    # itera tra gli elementi del database e controlla se esiste già una preferenza per quella chat
    for chat_tz in timezone_list:
        if chat_tz['chat_id'] == chat_id:
            return True
    # se non ha trovato nessuna preferenza restituisce falso
    return False


# riceve come argomento una stringa, restituisce un oggetto datetime.datetime
# traduce in datetime.datetime espressioni come 3 min, 3 h, 3 d, 01/01/01, 17:10 oppure 01/01/01 10:15
# get_time deve essere usato direttamente nella creazione dei contab job e non nel salvataggio sul db
def get_time(argument,chat_id):
    # scelgo il fuso orario dell'utente
    chosen_timezone = pytz.timezone(get_timezone(chat_id))
    utc=pytz.timezone('UTC')
    if len(argument) > 1:
        # se l'array argument contiene più di un argomento allora può essere sia timedelta che una data con sia giorno che ora oppure da errore
        if argument[1] == 'min' and is_int(argument[0]):
            data_notz = datetime.now() + timedelta(minutes=int(argument[0]))
            data_utc = utc.localize(data_notz)
            data = data_utc.astimezone(chosen_timezone)
        elif argument[1] == 'h' and is_int(argument[0]):
            data_notz = datetime.now() + timedelta(hours=int(argument[0]))
            data_utc = utc.localize(data_notz)
            data = data_utc.astimezone(chosen_timezone)
        elif argument[1] == 'd' and is_int(argument[0]):
            data_notz = datetime.now() + timedelta(days=int(argument[0]))
            data_utc = utc.localize(data_notz)
            data = data_utc.astimezone(chosen_timezone)
        elif is_date(f'{argument[0]} {argument[1]}'):
            data_notz = parse(f'{argument[0]} {argument[1]}')
            data = chosen_timezone.localize(data_notz)
        else:
            raise TypeError('Command argument was not written in a valid format')
    elif len(argument) == 1:
        # se l'array argument contiene un solo elemento deve essere per forza una data altrimenti da errore
        if is_date(argument[0]):
            data_notz = parse(argument[0])
            data = chosen_timezone.localize(data_notz)
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
        # genero l'id
        job_id = str(generate_id())

        #ottengo da get_time una data secondo il fuso orario dell'utente
        data_withtz=get_time(argument)
        # il container ha come fuso orario UTC quindi converto la data
        data = data_withtz.astimezone(pytz.utc)

        # aggiungere comando crontab
        scheduled_message = cron.new(
            command=crea_comando(TOKEN, update.message.reply_to_message.message_id,
                                 update.message.reply_to_message.chat.id,
                                 update.message.from_user.id), comment=job_id)
        scheduled_message.setall(data)
        cron.write()

        # altro comando crontab per eliminare la query scaduta dal database, necessario per avere una reminderslist aggiornata
        delete_scheduled_message = cron.new(command='/usr/local/bin/python3 /botREMINDbot/reminder_remove.py ' + job_id,
                                            comment=job_id)
        delete_scheduled_message.setall(data + timedelta(minutes=1))
        cron.write()

        db.insert({'job_id': job_id, 'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.from_user.id,
                   'data': data.strftime("%m/%d/%Y %H:%M:%S")})
        print(str({'job_id': job_id, 'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.from_user.id,
                   'data': data.strftime("%m/%d/%Y %H:%M:%S")}))
        # manda un messaggio per notificare che il reminder è stato impostato con successo
        context.bot.deleteMessage(update.message.chat.id, update.message.message_id)
        context.bot.send_message(update.message.from_user.id,
                                 f'Reminder has been successfully scheduled for {data_withtz.strftime("%m/%d/%Y %H:%M:%S")}.')
    except ValueError:
        print('Format not valid')
        context.bot.deleteMessage(update.message.chat.id, update.message.message_id)
        context.bot.send_message(update.message.from_user.id, 'Reminder format was not correct use /help for more.')


# remind di un messaggio direttamente nel gruppo
# salva in database id del messaggio, id della chat di provenienza,id del gruppo e data
# avverte sul gruppo se il reminder è salvato con successo o meno
def remindingroup(update, context):
    argument = estrai_argomento(update.message.text)
    try:
        # genero l'id
        job_id = str(generate_id())

        # aggiungo alla data inserita anche il fuso orario dell'utente
        data_notz = get_time(argument)
        chosen_timezone = pytz.timezone(get_timezone(update.message.chat.id))
        data_withtz = chosen_timezone.localize(data_notz)
        # il container ha come fuso orario UTC quindi converto la data
        data = data_withtz.astimezone(pytz.utc)

        # aggiungere comando crontab
        scheduled_message = cron.new(command=
                                     crea_comando(TOKEN, update.message.reply_to_message.message_id,
                                                  update.message.reply_to_message.chat.id,
                                                  update.message.chat.id), comment=job_id)
        scheduled_message.setall(data)
        cron.write()

        # altro comando crontab per eliminare la query scaduta dal database, necessario per avere una reminderslist aggiornata
        delete_scheduled_message = cron.new(command=f'/usr/local/bin/python3 /botREMINDbot/reminder_remove.py {job_id}',
                                            comment=job_id)
        print((data + timedelta(minutes=1)).strftime("%m/%d/%Y %H:%M:%S"))
        delete_scheduled_message.setall(data + timedelta(minutes=1))
        cron.write()

        db.insert({'job_id': job_id, 'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.chat.id,
                   'data': data.strftime("%m/%d/%Y %H:%M:%S")})
        print(str({'job_id': job_id, 'message_id': update.message.reply_to_message.message_id,
                   'from_chat_id': update.message.reply_to_message.chat.id, 'chat_id': update.message.chat.id,
                   'data': data.strftime("%m/%d/%Y %H:%M:%S")}))
        # manda un messaggio per notificare che il reminder è stato impostato con successo
        context.bot.send_message(update.message.chat.id,
                                 f'Reminder has been successfully scheduled for {data_withtz.strftime("%m/%d/%Y %H:%M:%S")}.')
    except TypeError:
        print('Format not valid')
        context.bot.send_message(update.message.chat.id, 'Reminder format was not correct use /help for more.')


# itera in db.all(), salva in lista gli id e le date di tutti i reminder che hanno come 'chat_id' la chat_id di chi
# ha eseguito il comando e infine invia lista
def reminderslist(update, context):
    lista_messaggi = db.all()
    lista = ''
    counter = 0

    for messaggio in lista_messaggi:
        if messaggio['chat_id'] == update.message.chat.id:
            lista = lista + '- id: ' + messaggio['job_id'] + ', scheduled for: ' + messaggio['data'] + '\n'
            counter += 1

    if counter == 0:
        context.bot.send_message(update.message.chat.id, f'You don\'t have any scheduled reminders.')
    else:
        context.bot.send_message(update.message.chat.id, f'You have {str(counter)} scheduled reminders:\n{lista}')


def removereminder(update, context):
    # estraggo l'id del reminder da eliminare
    job_id = estrai_argomento(update.message.text)[0]

    # elimino dal database il messaggio programmato che ha quell'id
    remove(job_id)

    # elimino i cron jobs che hanno come commento l'id del messaggio
    cron.remove_all(comment=job_id)
    cron.write()


def timezone(update, context):
    location_name = str(estrai_argomento(update.message.text))

    try:
        # initialize Nominatim API
        geolocator = Nominatim(user_agent="botremindbot_timezonefinder")

        # getting Latitude and Longitude
        location = geolocator.geocode(location_name)

        # pass the Latitude and Longitude
        # into a timezone_at
        # and it return timezone
        timezoneobj = TimezoneFinder()

        # returns the timezone (stringa)
        timezone_name = timezoneobj.timezone_at(lng=location.longitude, lat=location.latitude)

        # controllo che non ci sia già una preferenza di timezone
        if has_timezone(update.message.chat.id):
            Chat_tz = Query()
            # aggiorno preferenza database
            timezone_db.update({'timezone': timezone_name}, Chat_tz.chat_id == update.message.chat.id)
        else:
            # inserisco id chat e preferenza del fuso orario nel database
            timezone_db.insert({'chat_id': update.message.chat.id, 'timezone': timezone_name})

    except ValueError:
        print('Timezone format not valid:' + location_name)
        context.bot.send_message(update.message.chat.id, 'Timezone format was not correct use /help for more.')


def help(update, context):
    help_text = '''Hi, this bot helps you setting up reminders.
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
    context.bot.send_message(update.message.chat.id, help_text)


def main():
    upd = Updater(TOKEN, use_context=True)
    disp = upd.dispatcher

    disp.add_handler(CommandHandler("remindme", remindme))
    disp.add_handler(CommandHandler("remindingroup", remindingroup))
    disp.add_handler(CommandHandler("help", help))
    disp.add_handler(CommandHandler("start", help))
    disp.add_handler(CommandHandler("reminderslist", reminderslist))
    disp.add_handler(CommandHandler("removereminder", removereminder))
    disp.add_handler(CommandHandler("timezone", timezone))

    upd.start_polling()

    upd.idle()


if __name__ == '__main__':
    main()
