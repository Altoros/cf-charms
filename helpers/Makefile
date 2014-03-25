all: test

test: test_setup
	./bin/nosetests

test_setup:
	sudo apt-get install libapt-pkg-dev
	./bin/test_setup

lint:
	@echo "Lint check (flake8)"
	@flake8 --exclude .venv .


coverage:
	./bin/nosetests --with-coverage --cover-html --cover-html-dir=cover
	xdg-open cover/index.html

clean:
	rm -rf cover .venv


