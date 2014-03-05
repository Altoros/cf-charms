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
	juju deploy --repository=../../. local:trusty/cf-go-router --show-log
