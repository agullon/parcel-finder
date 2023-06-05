FROM alpine:3.14

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache setuptools

WORKDIR /usr/telegram-app/

COPY telegram-app/requirements.txt requirements.txt

RUN pip3 install --root-user-action=ignore -r requirements.txt

COPY telegram-app/main.py main.py
COPY telegram-app/screenshot.py screenshot.py

COPY /etc/telegram-bot-token/telegram-bot-token /etc/telegram-bot-token/telegram-bot-token
