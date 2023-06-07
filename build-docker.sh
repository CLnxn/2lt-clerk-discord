docker rm -f dbot
docker image rm discordbot
docker build --tag=discordbot .
docker volume create dbotvolume
docker run --name dbot \
-p 127.0.0.1:1339:1337 \
-v /home/mount/discordbot/data:/var/lib/mysql \
discordbot:latest
