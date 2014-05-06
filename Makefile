PROJECT = bautablink

SRC_DIR = debian
SITE_SRC_DIR = ../../web/_site
API_SRC_DIR = ../../api
BUILD_DIR = build/$(PROJECT)-deb

PACKAGE_NAME = $(PROJECT)
DEB = $(PACKAGE_NAME).deb

VERSION := 1-dev

SRC_FILES = $(shell find $(SRC_DIR) -type f)

.PHONY: all deb info install remove clean

all: deb

deb: $(DEB)

$(DEB): suppress-tags $(SRC_FILES)
	mkdir -p $(BUILD_DIR)
	cd $(SRC_DIR) && tar cf - . | ( cd - && cd $(BUILD_DIR) && tar xf - )

	mkdir -p $(BUILD_DIR)/bauta/web
	cd $(SITE_SRC_DIR) && tar cf - . | ( cd - && cd $(BUILD_DIR)/bauta/web && tar xf - )

	mkdir -p $(BUILD_DIR)/bauta/api
	cd $(API_SRC_DIR) && tar cf - . | ( cd - && cd $(BUILD_DIR)/bauta/api && tar xf - )

	find $(BUILD_DIR) -name '*.pyc' -delete

	echo "Version: $(VERSION)" >>$(BUILD_DIR)/DEBIAN/control
	find $(BUILD_DIR) -name '*~' -delete
	chmod -R g-w $(BUILD_DIR)
	fakeroot dpkg-deb --build $(BUILD_DIR) $(DEB) && lintian --suppress-tags-from-file suppress-tags $(DEB)

info: $(DEB)
	dpkg --info $(DEB)
	dpkg --contents $(DEB)

install: $(DEB)
	sudo dpkg -i $(DEB)

remove: $(DEB)
	sudo dpkg -r $(PACKAGE_NAME)

clean:
	rm -rf $(BUILD_DIR) $(DEB)
