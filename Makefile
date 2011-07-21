VERSION = 0.0.1
CONFIGDIR = /etc/osg

_default:
	@echo "Nothing to make. Try make install"

clean:
	@rm -f *~	

install:
	@if [ "$(DESTDIR)" = "" ]; then                                        \
		echo " ";                                                      \
		echo "ERROR: DESTDIR is required";                             \
		exit 1;                                                        \
	fi

	mkdir -p $(DESTDIR)/$(CONFIGDIR)
	install -p -m 644 ce.ini $(DESTDIR)/$(CONFIGDIR)/config.ini

dist:
	mkdir -p osg-configure-$(VERSION)
	cp -p Makefile ce.ini osg-configure-$(VERSION)/
	tar czf osg-configure-$(VERSION).tar.gz osg-configure-$(VERSION)/

release: dist
	@if [ "$(DESTDIR)" = "" ]; then                                        \
		echo " ";                                                      \
		echo "ERROR: DESTDIR is required";                             \
		exit 1;                                                        \
	fi
	mkdir -p $(DESTDIR)/osg-configure/$(VERSION)
	mv -f osg-configure-$(VERSION).tar.gz $(DESTDIR)/osg-configure/$(VERSION)/
	rm -rf osg-configure-$(VERSION)

	
