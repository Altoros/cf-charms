CHARM_DIR := $(shell pwd)
TEST_TIMEOUT := 900

test: lint 

lint:
	@echo "Lint check (flake8)"
	@flake8 --ignore=F401,E501\
	    hooks hooks/charmhelpers/cloudfoundry
clean:
	find . -name '*.pyc' -delete
	find . -name '*.bak' -delete

run:
ifdef m
	juju deploy --to $(m) --repository=../../. local:trusty/cf-go-router router --show-log
else
	juju deploy --repository=../../. local:trusty/cf-go-router router --show-log
endif
log:
	view -o ~/.juju/local/log/router-0-debug.log ~/.juju/local/log/unit-router-0.log
destroy:
	juju destroy-service router

