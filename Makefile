CONTAINER_ENGINE=$(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)
CURRENT_DIR=$(shell pwd)

DOCKER_REPO?=agullon
IMAGE_NAME?=parcel-finder
IMAGE_VERSION?=latest

run:
	$(CONTAINER_ENGINE) run --rm -p 4444 -e LOCALHOST='$(LOCALHOST)' $(DOCKER_REPO)/$(IMAGE_NAME):latest

run-local:
	$(CONTAINER_ENGINE) run --rm -p 4444 -e LOCALHOST='$(LOCALHOST)' $(DOCKER_REPO)/$(IMAGE_NAME):local

build:
	$(CONTAINER_ENGINE) build -t $(DOCKER_REPO)/$(IMAGE_NAME):latest -f Dockerfile .

build-local:
	$(CONTAINER_ENGINE) build -t $(DOCKER_REPO)/$(IMAGE_NAME):local -f Dockerfile.local .

push:
	$(CONTAINER_ENGINE) push $(DOCKER_REPO)/$(IMAGE_NAME):latest

k8s/create-secret:
	kubectl create secret generic regcred --from-file=.dockerconfigjson=/home/agullon/.docker/config.json --type=kubernetes.io/dockerconfigjson -n prod

deploy:
	kubectl create secret generic telegram-bot-token --from-file=/home/agullon/parcel-finder/telegram-bot-token -n prod
	kubectl apply -f k8s-manifests/telegram-bot.yaml -n prod

redeploy: remove deploy

rollout:
	kubectl rollout restart deployment -l name=parcel-finder -n prod

logs:
	kubectl logs -f -l name=parcel-finder -n prodi

describe:
	kubectl describe pod -l name=parcel-finder -n prod

remove:
	kubectl delete -f k8s-manifests/telegram-bot.yaml -n prod
	kubectl delete secret telegram-bot-token -n prod
	
