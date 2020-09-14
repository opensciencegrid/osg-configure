PYTHON = python
VERSION = $(shell $(PYTHON) -c "import sys; sys.path.insert(0, '.'); from osg_configure import version; print(version.__version__)")
NAME := osg-configure
PREFIX := /usr
BINDIR := $(PREFIX)/bin
SBINDIR := $(PREFIX)/sbin
SYSCONFDIR := /etc
DATAROOTDIR := $(PREFIX)/share
PYTHON_SITELIB := $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; import sys; sys.stdout.write(get_python_lib())")
UPSTREAM_SOFTWARE_DIR = /p/vdt/public/html/upstream/$(NAME)

echo:=@echo
echotbl:=@printf "%-30s %s\n"

help:
	$(echo) "Targets:"
	$(echo)
	$(echotbl) "install" "Install software onto local disk under DESTDIR"
	$(echotbl) "install-noconfig" "Install software onto local disk; leave configs in /etc alone"
	$(echotbl) "dist" "Create source tarball (don't run on AFS)"
	$(echotbl) "upstream" "Put source tarball in VDT upstream software dir (don't run on AFS)"
	$(echo)
	$(echo) "Variables:"
	$(echo)
	$(echotbl) "DESTDIR" "Root of where to install [$(DESTDIR)]"
	$(echotbl) "UPSTREAM_SOFTWARE_DIR" "Where to upload the source tarball [$(UPSTREAM_SOFTWARE_DIR)]"


install:
	$(PYTHON) setup.py install --root=$(DESTDIR)/ --prefix=$(PREFIX)
	mkdir -p  $(DESTDIR)$(SBINDIR)
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)

install-noconfig:
	$(PYTHON) setup.py install_lib install_scripts --root=$(DESTDIR)/ --prefix=$(PREFIX)
	mkdir -p  $(DESTDIR)$(SBINDIR)
	mv -f  $(DESTDIR)$(BINDIR)/$(NAME)  $(DESTDIR)$(SBINDIR)/$(NAME)

dist:
	-rm -f MANIFEST
	$(PYTHON) setup.py sdist

upstream: dist
	mkdir -p  $(UPSTREAM_SOFTWARE_DIR)/$(VERSION)
	sha1sum  dist/$(NAME)-$(VERSION).tar.gz
	cp -ip  dist/$(NAME)-$(VERSION).tar.gz  $(UPSTREAM_SOFTWARE_DIR)/$(VERSION)

.PHONY: help  install  install-noconfig  dist  upstream
