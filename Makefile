.PHONY: all detect install initsystem

prefix = /opt/Git-Auto-Deploy/

#init_version := $(shell /sbin/init --version 2>&1)
#test_upstart := $(shell printf $(init_version) | grep -q upstart || grep -q upstart /proc/net/unix ; echo $$?)
#test_systemd := $(shell printf $(init_version) | grep -q systemd || grep -q systemd /proc/1/comm || grep -q systemd /proc/net/unix ; echo $$?)

PYTHON       ?= python2

# Default debian dist (override using make <target> DIST=<debian dist>)
DIST=trusty

# Package name and version
PACKAGE_NAME=$(shell python setup.py --name)
PACKAGE_VERSION=$(shell python setup.py --version)

define version =
    echo "hello"
    exit 1
endef

all:

clean: clean-pypi clean-deb
	rm -rf *.tar.gz

clean-pypi:
	rm -rf *.egg-info
	rm -rf dist/pypi
	if [ -d "dist" ]; then rmdir --ignore-fail-on-non-empty dist; fi

pypi:
	$(PYTHON) setup.py sdist --dist-dir dist/pypi

upload-pypi:
	$(PYTHON) setup.py sdist --dist-dir dist/pypi register upload -r pypi

clean-deb:
	rm -rf dist/deb
	rm -f dist/*.tar.gz
	if [ -d "dist" ]; then rmdir --ignore-fail-on-non-empty dist; fi

# Usage: make deb-source [DIST=<debian dist>]
deb-source: clean-deb
	# Make a debian source package using stdeb
	python setup.py --command-packages=stdeb.command sdist_dsc -x platforms/debian/stdeb.cfg --dist-dir dist/deb --debian-version $(DIST) --suite $(DIST)
	# Copy debian package config files
	cp -vr platforms/debian/stdeb/* dist/deb/$(PACKAGE_NAME)-$(PACKAGE_VERSION)/debian/

deb: clean-deb deb-source
	# Build .deb package (without signing)
	cd dist/deb/$(PACKAGE_NAME)-$(PACKAGE_VERSION); \
	dpkg-buildpackage -rfakeroot -uc -us

signed-deb: clean-deb deb-source
	# Build .deb package (signed)
	cd dist/deb/$(PACKAGE_NAME)-$(PACKAGE_VERSION); \
	debuild -S -sa

upload-deb: clean-deb signed-deb
	# Upload signed debian package to ppa
	#cd dist/deb/$(PACKAGE_NAME)-$(PACKAGE_VERSION); \
	dput ppa:olipo186/$(PACKAGE_NAME) dist/deb/$(PACKAGE_NAME)_$(PACKAGE_VERSION)-$(DIST)_source.changes


#initsystem:
#ifeq ($(test_upstart),0)
#	@echo "Upstart detected!"
#else ifeq ($(test_systemd),0)
#	@echo "Systemd detected!"
#else
#	@echo "InitV supposed"
#endif
#	@echo "Init script not installed - not yet implemented"

#install: clean all
#	@echo "Installing deploy script in $(prefix) ..."
#	@echo "Installing deploy script in $(init_version) ..."
#	@sudo mkdir $(prefix) &> /dev/null || true
#	@sudo cp config.json.sample $(prefix)config.json
#	@sudo cp -r gitautodeploy $(prefix)/
#
#	@echo "Installing run-on-startup scripts according to your init system ..."
#	@make initsystem
