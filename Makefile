NAME := osg-configure
PREFIX := /usr
BINDIR := $(PREFIX)/bin
SBINDIR := $(PREFIX)/sbin
SYSCONFDIR := /etc
DATAROOTDIR := $(PREFIX)/share
PYTHON_SITELIB := $(shell python -c "from distutils.sysconfig import get_python_lib; import sys; sys.stdout.write(get_python_lib())")

_default:
	@echo "Nothing to make. Try 'make install'."


install:
	python setup.py install --root=$(DESTDIR)/
	mkdir -p  $(DESTDIR)$(SBINDIR)
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)
	ln -snf  $(SBINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/configure-osg

install-noconfig:
	python setup.py install_lib install_scripts
	mkdir -p  $(DESTDIR)$(SBINDIR)
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)
	ln -snf  $(SBINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/configure-osg

install-3.1:
	@echo "OSG 3.1 is unsupported."
	@exit 1

install-3.2: install

install-3.3: install

dist:
	rm -f MANIFEST
	python setup.py sdist

.PHONY: _default  install  install-3.1  install-3.2  install-3.3 install-noconfig dist
