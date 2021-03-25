# botREMINDbot
Telegram bot to remind later messages.
## Deploy with Docker
```
docker build --build-arg TOKEN=YOUR_BOT_TOKEN -t botremindbot . 
```
```
docker run -v /path/to/database/folder:/database --name botremindbot -t -i botremindbot --restart unless-stopped
```
