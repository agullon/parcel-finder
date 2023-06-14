CONTAINER_ENGINE=$(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)
CURRENT_DIR=$(shell pwd)

DOCKER_REPO?=agullon
IMAGE_NAME?=parcel-finder
IMAGE_VERSION?=latest

run-bot:
	$(CONTAINER_ENGINE) run --rm -p 4444 -e TELEGRAM_BOT_TOKEN=$(shell cat telegram-bot-token) $(DOCKER_REPO)/$(IMAGE_NAME):latest python3 telegram-app/main.py

run-seleniumhub:
	$(CONTAINER_ENGINE) run --rm -it -p 4444:4444 -p 5900:5900 -p 7900:7900 --shm-size 2g seleniarm/standalone-chromium:latest

build:
	$(CONTAINER_ENGINE) build -t $(DOCKER_REPO)/$(IMAGE_NAME):latest -f Dockerfile .

push:
	$(CONTAINER_ENGINE) push $(DOCKER_REPO)/$(IMAGE_NAME):latest

