CONTAINER_ENGINE=$(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)
CURRENT_DIR=$(shell pwd)

DOCKER_REPO?=agullon
IMAGE_NAME?=parcel-finder
IMAGE_VERSION?=latest

run-parcel-finder:
	$(CONTAINER_ENGINE) run -d --name parcel-finder --rm -e TELEGRAM_BOT_TOKEN=$(shell cat telegram-bot-token) -e SELENIUM_HUB_IP=192.168.1.40 $(DOCKER_REPO)/$(IMAGE_NAME):latest python3 telegram-app/main.py

stop-parcel-finder:
	$(CONTAINER_ENGINE) stop parcel-finder

run-selenium-hub:
	$(CONTAINER_ENGINE) run -d --name selenium-hub --rm -it -p 4444:4444 -p 5900:5900 -p 7900:7900 --shm-size 2g seleniarm/standalone-chromium:latest

stop-selenium-hub:
	$(CONTAINER_ENGINE) stop parcel-finder

build:
	$(CONTAINER_ENGINE) build -t $(DOCKER_REPO)/$(IMAGE_NAME):latest -f Dockerfile .

