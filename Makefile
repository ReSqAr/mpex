test:
	python3 test.py

coverage:
	python3 -m coverage erase
	python3 -m coverage run --source=.,lib test.py
	python3 -m coverage html

sdist:
	python3 setup.py sdist
