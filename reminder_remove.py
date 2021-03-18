# riceve come argomento il job_id
# elimina nel database il reminder corrispondente

from tinydb import TinyDB, Query
import sys


job_id = str(sys.argv[1])
db = TinyDB('/database/botREMINDbot_db.json')
Messaggio = Query()
db.remove(Messaggio['job_id'] == job_id)
