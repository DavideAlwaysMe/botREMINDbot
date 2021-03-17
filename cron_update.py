from crontab import CronTab
from tinydb import TinyDB, Query
from main import crea_comando
from dateutil.parser import parse
from datetime import datetime
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
    print(messaggio['data'])
    if (parse(messaggio['data']) < datetime.now()):
        print(messaggio['data'])
        # elimino messsaggio dal database se scaduto
        db.remove(Messaggio['data'] == messaggio['data'])
    else:
        # aggiungere comando crontab
        data = parse(messaggio.data)
        scheduled_message = cron.new(
            command=crea_comando(TOKEN,messaggio.message_id, messaggio.from_chat_id, messaggio.chat))
        scheduled_message.setall(data)
        cron.write()
