CHARM_DIR := $(shell pwd)
TEST_TIMEOUT := 900

test: lint 

lint:
	@echo "Lint check (flake8)"
	@flake8 --exclude=hooks/charmhelpers hooks 
clean:
	find . -name '*.pyc' -delete
	find . -name '*.bak' -delete
run: lint deploy
vlog:
	view ~/.juju/local/log/unit-dea-0.log
log:
	tail -f ~/.juju/local/log/unit-dea-0.log
destroy:
	juju destroy-service dea
deploy:

ifdef m
	juju deploy --to $(m) --repository=../../. local:trusty/cf-dea dea --show-log
else
	juju deploy --repository=../../. local:trusty/cf-dea dea --show-log
endif
upgrade:
	juju upgrade-charm --repository=../../. dea --show-log
js:
	juju status
jss:
	juju status dea
