# set base image (host OS)
FROM python:3.8

#clono il repository
RUN git clone https://github.com/DavideAlwaysMe/botREMINDbot.git

# set the working directory in the container
WORKDIR /botREMINDbot

#il token del bot è passato come parametro nel comando di esecuzione del bot
ARG TOKEN
ENV TOKEN ${TOKEN}

#rendo eseguibile il file che contiene le istruzioni da eseguire all'avvio del container
RUN chmod +x start.sh

#installo crontab
RUN apt-get update && apt-get -y install cron

# install dependencies
RUN pip3 install -r requirements.txt

#avviare il bot e aggiornare il crontab
CMD ["sh", "-c", "/botREMINDbot/start.sh ${TOKEN} root"]