SUBDIRS=lib

PYFILES= *.py

test:
	python3 test.py

coverage:
	python3 -m coverage erase
	python3 -m coverage run --source=.,lib test.py
	python3 -m coverage html

install:
	mkdir -p $(DESTDIR)/usr/lib/python3/dist-packages/mpex/ $(DESTDIR)/usr/bin/
	cp $(PYFILES) $(DESTDIR)/usr/lib/python3/dist-packages/mpex/
	cp mpex-bin $(DESTDIR)/usr/bin/mpex
	for i in $(SUBDIRS); do make DESTDIR=$(DESTDIR) -C $$i install; done

subdirs:
	for i in $(SUBDIRS); do make -C $$i; done

