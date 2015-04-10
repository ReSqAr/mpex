SUBDIRS=lib

PYFILES= *.py

install:
	mkdir -p $(DESTDIR)/usr/lib/python3/dist-packages/mpex/ $(DESTDIR)/usr/bin/
	cp $(PYFILES) $(DESTDIR)/usr/lib/python3/dist-packages/mpex/
	cp mpex-bin $(DESTDIR)/usr/bin/mpex
	for i in $(SUBDIRS); do make DESTDIR=$(DESTDIR) -C $$i install; done

subdirs:
	for i in $(SUBDIRS); do make -C $$i; done

