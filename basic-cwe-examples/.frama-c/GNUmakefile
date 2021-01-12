# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC)-config -print-share-path)/analysis-scripts/prologue.mk
###############################################################################

# Edit below as needed. MACHDEP is mandatory. Suggested flags are optional.

MACHDEP = x86_64

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \

## General flags
FCFLAGS     += \
  -add-symbolic-path=..:. \
  -kernel-warn-key annot:missing-spec=abort \
  -kernel-warn-key typing:implicit-function-declaration=abort \

# (Optional) Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \

## Analysis targets (suffixed with .eva)
IMPRECISE_TARGETS = cwe20.eva cwe20-2.eva cwe119.eva cwe190.eva cwe416.eva cwe787.eva

PRECISE_TARGETS = $(subst .eva,-precise.eva,$(IMPRECISE_TARGETS))

TARGETS = $(IMPRECISE_TARGETS) $(PRECISE_TARGETS)

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites
cwe20.parse:  ../cwe20.c
cwe20-2.parse:  ../cwe20-2.c
cwe119.parse: ../cwe119.c
cwe190.parse: ../cwe190.c
cwe416.parse: ../cwe416.c
cwe787.parse: ../cwe787.c

cwe20-precise.parse:  ../cwe20.c
cwe20-2-precise.parse:  ../cwe20-2.c
cwe119-precise.parse: ../cwe119.c
cwe190-precise.parse: ../cwe190.c
cwe416-precise.parse: ../cwe416.c
cwe787-precise.parse: ../cwe787.c

cwe20-precise.eva:   EVAFLAGS +=
cwe20-2-precise.eva: EVAFLAGS += -eva-precision 5
cwe119-precise.eva:  EVAFLAGS +=
cwe190-precise.eva:  EVAFLAGS += -warn-unsigned-overflow
cwe416-precise.eva:  EVAFLAGS +=
cwe787-precise.eva:  EVAFLAGS += -eva-precision 2

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC)-config -print-share-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
