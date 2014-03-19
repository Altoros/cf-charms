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
log:
	tail -f ~/.juju/local/log/unit-nats-0.log
deploy:

ifdef m
	juju deploy --to $(m) --repository=../../. local:trusty/cf-nats nats --show-log
else
	juju deploy --repository=../../. local:trusty/cf-nats nats --show-log
endif
upgrade:
	juju upgrade-charm --repository=../../. nats --show-log
