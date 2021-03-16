from crontab import CronTab
from tinydb import TinyDB, Query
from main import get_time, crea_comando
from datetime import datetime
import sys

# il bot deve essere eseguito con docker, sarà contenuto nella cartella /botREMINDbot e il suo database in /database
db = TinyDB('/database/botREMINDbot_db.json')
lista_messaggi = db.all()
Messaggio = Query()

# token fornito dal BotFather passato come argomento del comando di esecuzione del bot
TOKEN = sys.argv[1]
# user passato come parametro
USER = sys.argv[2]

# il bot programma l'invio dei messaggi con crontab
cron = CronTab(user=USER)

for messaggio in lista_messaggi:
    if (get_time(messaggio['data']) < datetime.now()):
        # elimino messsaggio dal database se scaduto
        db.remove(Messaggio.data == messaggio['data'])
    else:
        # aggiungere comando crontab
        data = get_time(messaggio.data)
        scheduled_message = cron.new(
            command=crea_comando(TOKEN,messaggio.message_id, messaggio.from_chat_id, messaggio.chat))
        scheduled_message.setall(data)
        cron.write()
