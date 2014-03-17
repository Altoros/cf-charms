CHARM_DIR := $(shell pwd)
TEST_TIMEOUT := 900

test: lint 

lint:
	@echo "Lint check (flake8)"
	@flake8 --exclude=hooks/charmhelpers hooks
clean:
	find . -name '*.pyc' -delete
	find . -name '*.bak' -delete
run:
ifdef m
	juju deploy --to $(m) --repository=../../. local:trusty/cf-cloud-controller cc --show-log
else
	juju deploy --repository=../../. local:trusty/cf-cloud-controller cc --show-log
endif
log:
	tail -f ~/.juju/local/log/unit-cc-0.log
destroy:
	juju destroy-service cc
