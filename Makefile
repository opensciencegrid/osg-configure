VERSION = $(shell python -c "import sys; sys.path.insert(0, '.'); from osg_configure import version; print(version.__version__)")
NAME := osg-configure
PREFIX := /usr
BINDIR := $(PREFIX)/bin
SBINDIR := $(PREFIX)/sbin
SYSCONFDIR := /etc
DATAROOTDIR := $(PREFIX)/share
PYTHON_SITELIB := $(shell python -c "from distutils.sysconfig import get_python_lib; import sys; sys.stdout.write(get_python_lib())")
UPSTREAM_SOFTWARE_DIR = /p/vdt/public/html/upstream/$(NAME)

_default:
	@echo "Nothing to make. Try 'make install'."


install:
	python setup.py install --root=$(DESTDIR)/
	mkdir -p  $(DESTDIR)$(SBINDIR)
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)

install-noconfig:
	python setup.py install_lib install_scripts
	mkdir -p  $(DESTDIR)$(SBINDIR)
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)

dist:
	rm -f MANIFEST
	python setup.py sdist

upstream: dist
	mkdir -p  $(UPSTREAM_SOFTWARE_DIR)/$(VERSION)
	sha1sum  dist/$(NAME)-$(VERSION).tar.gz
	cp -p  dist/$(NAME)-$(VERSION).tar.gz  $(UPSTREAM_SOFTWARE_DIR)/$(VERSION)

.PHONY: _default  install  install-noconfig  dist  upstream
