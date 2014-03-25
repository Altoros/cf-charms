all: test

test: test_setup
	./bin/nosetests

test_setup:
	sudo apt-get install libapt-pkg-dev
	./bin/test_setup

lint:
	@echo "Lint check (flake8)"
	@flake8 --exclude .venv .



