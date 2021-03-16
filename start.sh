#!/bin/bash

echo $1 $2
python3 main.py $1 $2
python3 cron_update.py $1 $2