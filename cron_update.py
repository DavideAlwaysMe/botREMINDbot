from crontab import CronTab
from tinydb import TinyDB, Query
from main import crea_comando
from dateutil.parser import parse
from datetime import datetime, timedelta
import sys

# il bot deve essere eseguito con docker, sarà contenuto nella cartella /botREMINDbot e il suo database in /database
db = TinyDB('/database/botREMINDbot_db.json')
lista_messaggi = db.all()
Messaggio = Query()

# token fornito dal BotFather passato come argomento del comando di esecuzione del bot
TOKEN = str(sys.argv[1])
# user passato come parametro
USER = sys.argv[2]

# il bot programma l'invio dei messaggi con crontab
cron = CronTab(user=USER)

for messaggio in lista_messaggi:
    print('Found scheduled message in database ' + messaggio['data'])
    if (parse(messaggio['data']) < datetime.now()):
        print('Deleted old message scheduled for ' + messaggio['data'])
        # elimino messsaggio dal database se scaduto
        db.remove(Messaggio['data'] == messaggio['data'])
    else:
        # aggiungere comando crontab
        data = parse(messaggio['data'])

        scheduled_message = cron.new(
            command=crea_comando(TOKEN, messaggio['message_id'], messaggio['from_chat_id'], messaggio['chat_id']),
            comment=messaggio['job_id'])
        scheduled_message.setall(data)
        cron.write()

        # altro comando crontab per eliminare la query scaduta dal database, necessario per avere una reminderslist aggiornata
        delete_scheduled_message = cron.new(command='/usr/local/bin/python3 /botREMINDbot/reminder_remove.py ' + messaggio['job_id'],
                                            comment='delete ' + messaggio['job_id'])
        delete_scheduled_message.setall(data + timedelta(minutes=1))
        cron.write()

        print('Succesfully scheduled reminder found in database')
