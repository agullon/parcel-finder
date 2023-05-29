FROM alpine:3.14

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

WORKDIR /usr/app

COPY requirements.txt requirements.txt

RUN pip install --root-user-action=ignore -r requirements.txt

COPY main.py main.py
COPY screenshot.py screenshot.py

EXPOSE 5050
