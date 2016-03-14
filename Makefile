
REPO := $(shell cd ..; pwd)

CHARMS=wallabag

all: $(CHARMS:%=$(REPO)/trusty/%)

upload: $(CHARMS:%=upload-%)

upload-%:
	charm2 upload $(REPO)/trusty/$* cs:~cmars/trusty/$*

publish: $(CHARMS:%=publish-%)

publish-%:
	charm2 publish cs:~cmars/trusty/$*

$(REPO)/trusty/%:
	JUJU_REPOSITORY=$(REPO) charm build .

clean:
	$(RM) -r $(CHARMS:%=$(REPO)/trusty/%)

.PHONY: all clean upload publish $(CHARMS:%=upload-%) $(CHARMS:%=publish-%)

