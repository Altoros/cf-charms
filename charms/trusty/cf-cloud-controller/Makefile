CHARM_DIR := $(shell pwd)
TEST_TIMEOUT := 900

test: lint 

lint:
	@echo "Lint check (flake8)"
	@flake8 --ignore=F401,E501\
	    hooks tests 
