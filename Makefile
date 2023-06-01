CONTAINER_ENGINE=$(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)
CURRENT_DIR=$(shell pwd)

DOCKER_REPO?=agullon
IMAGE_NAME?=parcel-finder
IMAGE_VERSION?=latest

run:
	python3 src/main.py

build:
	$(CONTAINER_ENGINE) build -t $(DOCKER_REPO)/$(IMAGE_NAME):$(IMAGE_VERSION) src

push:
	$(CONTAINER_ENGINE) push $(DOCKER_REPO)/$(IMAGE_NAME):$(IMAGE_VERSION)

k8s/create-secret:
	kubectl create secret generic regcred --from-file=.dockerconfigjson=/home/agullon/.docker/config.json --type=kubernetes.io/dockerconfigjson -n prod

deploy:
	kubectl create secret generic telegram-bot-token --from-file=/home/agullon/parcel-finder/telegram-bot-token -n prod
	kubectl apply -f k8s-manifest/deployment.yaml -n prod

redeploy: remove deploy

rollout:
	kubectl rollout restart deployment -l name=parcel-finder -n prod

logs:
	kubectl logs -f -l name=parcel-finder -n prod
describe:
	kubectl describe pod -l name=parcel-finder -n prod
remove:
	kubectl delete deploy parcel-finder-deployment -n prod
	kubectl delete pod -l name=parcel-finder -n prod
	kubectl delete secret telegram-bot-token -n prod
	
