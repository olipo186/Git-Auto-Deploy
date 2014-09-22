.PHONY: all detect install initsystem

prefix = /opt/Gitlab_Auto_Deploy/

init_version := $(shell init --version 2>&1)
test_upstart := $(shell printf $(init_version) | grep upstart | wc -l)
test_systemd := $(shell printf $(init_version) | grep systemd | wc -l)
test_initv   := $(shell printf $(init_version) | grep invalid | wc -l)

all:

clean:

initsystem:
ifeq ($(test_upstart),1)
	@echo "Upstart detected!"
else ifeq ($(test_systemd),1)
	@echo "Systemd detected!"
else ifeq ($(test_initv),1)
	@echo "InitV detected!"
else
	@echo "Error. Can't detect init system!"
endif
	@echo "Done!"

install: clean all
	@echo "Installing deploy script in $(prefix) ..."
	@sudo mkdir $(prefix) &> /dev/null || true
	@sudo cp GitAutoDeploy.conf.json.example $(prefix)GitAutoDeploy.conf.json
	@sudo cp GitAutoDeploy.py $(prefix)
	@sudo chmod +x $(prefix)GitAutoDeploy.py
	
	@echo "Installing run-on-startup scripts according to your init system ..."
	@make --silent initsystem
