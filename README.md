# Parcela Finder
This is a Telegram bot with a few actions to get info and navigate to a parcel in Mombuey, Valparaíso or Fresno de la Carballeda.

## Requisites
- Python3.9

## How to deploy it
Build container and run bot container and selenium hub container with Make targets:
1. `make build`
1. `make run-parcel-finder`
1. `make run-selenium-hub`

## How to run it for debugging
1. Create a python virtual env: `python3 -m venv env`
1. Activate virtual environment: `source env/bin/activate`
1. Install pip dependencies: `pip install -r src/requirements.txt`
1. Export Telegram bot token: `export TELEGRAM_BOT_TOKEN="123456:xxxxxxxxxxxx"`
1. Run bot: `python3 telegram-app/main.py`


## Dependecies
The data and images form the parcels are from:
- Visor IDECyL: https://idecyl.jcyl.es/vcig
- Visor SigPac: https://sigpac.mapa.gob.es/fega/visor/
