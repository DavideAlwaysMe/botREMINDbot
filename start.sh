#!/bin/bash

#clono il repository
rm -r botREMINDbot
git clone https://github.com/DavideAlwaysMe/botREMINDbot.git
echo $1 $2
python3 /botREMINDbot/cron_update.py $1 $2
python3 /botREMINDbot/main.py $1 $2