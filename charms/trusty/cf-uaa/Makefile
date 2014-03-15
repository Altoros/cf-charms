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
	view ~/.juju/local/log/unit-uaa-0.log
log:
	tail -f ~/.juju/local/log/unit-uaa-0.log
destroy:
	juju destroy-service uaa
deploy:

ifdef m
	juju deploy --to $(m) --repository=../../. local:trusty/cf-uaa uaa --show-log
else
	juju deploy --repository=../../. local:trusty/cf-uaa uaa --show-log
endif
upgrade:
	juju upgrade-charm --repository=../../. uaa --show-log
