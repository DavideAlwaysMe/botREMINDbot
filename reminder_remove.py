# riceve come argomento il job_id
# elimina nel database il reminder corrispondente

from tinydb import TinyDB, Query
import sys

#uso una funzione perchè lo userò anche per il comando /removereminder
def remove(job_id):
    db = TinyDB('/database/botREMINDbot_db.json')
    Messaggio = Query()
    db.remove(Messaggio['job_id'] == job_id)

def main():
    job_id = str(sys.argv[1])
    remove(job_id)

if __name__ == '__main__':
    main()