# Parcela Finder
This is a Telegram bot with a few actions to get info and navigate to a parcel in Mombuey, Valparaíso or Fresno de la Carballeda.

## Requisites
- Python3.9

## How to run it
1. Create a python virtual env: `python3 -m venv env`
1. Activate virtual environment: `source env/bin/activate`
1. Install pip dependencies: `pip install -r src/requirements.txt`
1. Export Telegram bot token: `echo 12345 > /etc/telegram-bot-token/telegram-bot-token`
1. Run bot: `python3 src/main.py`


## Dependecies
The data and images form the parcels are from:
- Visor IDECyL: https://idecyl.jcyl.es/vcig
- Visor SigPac: https://sigpac.mapa.gob.es/fega/visor/
