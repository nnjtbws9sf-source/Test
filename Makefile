PREFIX ?= /usr/local
BINDIR  = $(PREFIX)/bin
DATADIR = $(PREFIX)/share/space_shooter

.PHONY: run install uninstall

run:
	@./space_shooter

install:
	install -d $(DATADIR)
	install -m 644 entities.py game.py $(DATADIR)/
	install -m 644 main.py $(DATADIR)/
	@printf '#!/usr/bin/env bash\nexec python3 $(DATADIR)/main.py "$$@"\n' \
		> $(BINDIR)/space_shooter
	chmod +x $(BINDIR)/space_shooter
	@echo "Installed to $(BINDIR)/space_shooter"

uninstall:
	rm -f  $(BINDIR)/space_shooter
	rm -rf $(DATADIR)
	@echo "Uninstalled."
