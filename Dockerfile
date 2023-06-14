FROM debian

RUN apt-get update

RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install --no-cache setuptools --break-system-packages

WORKDIR /usr/telegram-app/

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt --break-system-packages

COPY telegram-app telegram-app

