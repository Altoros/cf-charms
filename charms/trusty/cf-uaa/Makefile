CHARM_DIR := $(shell pwd)
TEST_TIMEOUT := 900

test: lint 

lint:
	@echo "Lint check (flake8)"
	@flake8 --ignore=F401,E501\
	    hooks tests
clean:
	find . -name '*.pyc' -delete
	find . -name '*.bak' -delete
run:
ifdef m
	juju deploy --to $(m) --repository=../../. local:trusty/cf-uaa uaa --show-log
else
	juju deploy --repository=../../. local:trusty/cf-uaa uaa --show-log
endif
log:
	tail -f ~/.juju/local/log/unit-uaa-0.log
destroy:
	juju destroy-service uaa
	