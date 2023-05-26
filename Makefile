CONTAINER_ENGINE=$(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)
CURRENT_DIR=$(shell pwd)

DOCKER_REPO?=agullon
IMAGE_NAME?=parcel-finder
IMAGE_VERSION?=latest

run/main:
	$(CONTAINER_ENGINE) run $(DOCKER_REPO)/$(IMAGE_NAME):$(IMAGE_VERSION) python main.py

build:
	$(CONTAINER_ENGINE) build -t $(DOCKER_REPO)/$(IMAGE_NAME):$(IMAGE_VERSION) .

push:
	$(CONTAINER_ENGINE) push $(DOCKER_REPO)/$(IMAGE_NAME):$(IMAGE_VERSION)

deploy:
	kubectl create secret generic regcred --from-file=.dockerconfigjson=/home/agullon/.docker/config.json --type=kubernetes.io/dockerconfigjson -n prod
	kubectl create secret generic telegram-bot-token --from-file=ssh-privatekey=/home/agullon/.docker/telegram-bot-token -n prod
	kubectl apply -f deployment.yaml -n prod

rollout:
	kubectl rollout restart deployment -l project=telegram -n prod
