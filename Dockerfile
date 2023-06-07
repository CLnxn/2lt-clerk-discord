FROM python:3.11.3-alpine

RUN apk add --no-cache --update mariadb mariadb-client mariadb-connector-c-dev supervisor
 

RUN mkdir -p /app
RUN mkdir -p /var/lib/mysql

WORKDIR /app

COPY src .
COPY requirements.txt .
COPY /config/supervisord.conf /etc/supervisord.conf


EXPOSE 1337
ENV PYTHONDONTWRITEBYTECODE=1


RUN python -m pip install -r requirements.txt

COPY --chown=root entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]



