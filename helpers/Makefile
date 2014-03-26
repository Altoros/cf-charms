all: test

test: test_setup
	@./bin/nosetests

test_setup:
	@./bin/test_setup

lint:
	@echo "Lint check (flake8)"
	@flake8 --exclude .venv .


coverage:
	./bin/nosetests --with-coverage --cover-html --cover-html-dir=cover --cover-package=helpers
	xdg-open cover/index.html

clean:
	rm -rf cover .venv


