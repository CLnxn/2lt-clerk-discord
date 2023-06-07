docker rm -f dbot
docker image rm discordbot
@REM docker volume rm dbotvolume
docker build --tag=discordbot .
docker volume create dbotvolume 
docker run --name dbot -v dbotvolume:/var/lib/mysql discordbot:latest
