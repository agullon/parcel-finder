FROM debian

ENV PYTHONUNBUFFERED=1
RUN apt-get update

RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install --no-cache setuptools

WORKDIR /usr/telegram-app/

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY telegram-app telegram-app

