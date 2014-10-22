NAME := osg-configure
PREFIX := /usr
BINDIR := $(PREFIX)/bin
SBINDIR := $(PREFIX)/sbin
SYSCONFDIR := /etc
DATAROOTDIR := $(PREFIX)/share
PYTHON_SITELIB := $(shell python -c "from distutils.sysconfig import get_python_lib; import sys; sys.stdout.write(get_python_lib())")

_default:
	@echo "Nothing to make. Try `make install' or `make install-3.1'."


install-common:
	python setup.py install --root=$(DESTDIR)/
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)
	ln -snf  $(SBINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/configure-osg

install-3.1: install-common

install-3.2: install

install: install-common
	-rm -f  $(DESTDIR)$(PYTHON_SITELIB)/$(NAME)/configure_modules/cemon.py*
	-rm -rf  $(DESTDIR)$(DATAROOTDIR)/$(NAME)/tests/configs/cemon
	-rm -rf  $(DESTDIR)$(DATAROOTDIR)/$(NAME)/tests/test_cemon.*
	-rm -f  $(DESTDIR)$(SYSCONFDIR)/osg/config.d/30-cemon.ini

.PHONY: _default  install  install-common  install-3.1  install-3.2
