FRAMAC_DIR=../../frama-c/build/bin
ifeq ($(wildcard $(FRAMAC_DIR)),)
# Frama-C not installed locally; using the version in the PATH
else
export OCAMLPATH := $(FRAMAC_DIR)/../lib:$(OCAMLPATH)
FRAMAC=$(FRAMAC_DIR)/frama-c
FRAMAC_GUI=$(FRAMAC_DIR)/frama-c-gui
endif
