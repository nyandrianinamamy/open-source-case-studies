FRAMAC_BIN=/home/andr/git/frama-c-9-all-plugins/bin
ifeq ($(wildcard $(FRAMAC_BIN)),)
# Frama-C not installed locally; using the version in the PATH
else
FRAMAC=$(FRAMAC_BIN)/frama-c
FRAMAC_GUI=$(FRAMAC_BIN)/frama-c-gui
endif
