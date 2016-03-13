.PHONY: all detect install initsystem

prefix = /opt/Git-Auto-Deploy/

init_version := $(shell /sbin/init --version 2>&1)
test_upstart := $(shell printf $(init_version) | grep -q upstart || grep -q upstart /proc/net/unix ; echo $$?)
test_systemd := $(shell printf $(init_version) | grep -q systemd || grep -q systemd /proc/1/comm || grep -q systemd /proc/net/unix ; echo $$?)

all:

clean:

initsystem:
ifeq ($(test_upstart),0)
	@echo "Upstart detected!"
else ifeq ($(test_systemd),0)
	@echo "Systemd detected!"
else
	@echo "InitV supposed"
endif
	@echo "Init script not installed - not yet implemented"

install: clean all
	@echo "Installing deploy script in $(prefix) ..."
	@echo "Installing deploy script in $(init_version) ..."
	@sudo mkdir $(prefix) &> /dev/null || true
	@sudo cp config.json.sample $(prefix)config.json
	@sudo cp -r gitautodeploy $(prefix)/

	@echo "Installing run-on-startup scripts according to your init system ..."
	@make initsystem

