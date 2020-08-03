# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC)-config -scripts)/prologue.mk
###############################################################################

# Edit below as needed. MACHDEP is mandatory. Suggested flags are optional.

MACHDEP = x86_32

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \
  -includefc_stubs.h -D__FRAMAC__EVA \

## General flags
FCFLAGS     += \
  -add-symbolic-path=.:.. \
  -kernel-warn-key typing:implicit-function-declaration=abort \

## Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \
  -eva-no-alloc-returns-null \
  -main eva_main \
  -slevel 2 \

## GUI-only flags
FCGUIFLAGS += \
  -add-symbolic-path=.:.. \

## Analysis targets (suffixed with .eva)
TARGETS = kilo.eva

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites
kilo.parse: \
  ../kilo.c \
  fc_stubs.c \

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC)-config -scripts)/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
