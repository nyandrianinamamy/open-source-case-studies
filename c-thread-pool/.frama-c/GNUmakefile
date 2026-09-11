# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC) -print-lib-path)/analysis-scripts/prologue.mk
###############################################################################

# Edit below as needed. Suggested flags are optional.

MACHDEP = x86_32

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \
  -CC \

## General flags
FCFLAGS     += \
  -add-symbolic-path=..:. \
  -kernel-warn-key annot:missing-spec=abort \
  -kernel-warn-key typing:implicit-function-declaration=abort \
  -mt-threads-lib pthreads \

## Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \
  -eva-verbose 3 \
  -eva-precision 5 \
  -mthread \

## GUI-only flags
FCGUIFLAGS += \

## Analysis targets (suffixed with .eva))
TARGETS = \
  cThreadPool.eva \
  ex_api.eva \
  ex_conc_increment.eva \
  ex_no_work.eva \
  ex_nonzero_heap_stack.eva \
  ex_pause_resume.eva \
  ex_wait.eva \

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites
cThreadPool.parse: \
  ../example.c \
  ../thpool.c \

ex_api.parse: \
  ../tests/src/api.c \
  ../thpool.c \

ex_conc_increment.parse: \
  ../tests/src/conc_increment.c \
  ../thpool.c \

ex_no_work.parse: \
  ../tests/src/no_work.c \
  ../thpool.c \

ex_nonzero_heap_stack.parse: \
  ../tests/src/nonzero_heap_stack.c \
  ../thpool.c \

ex_pause_resume.parse: \
  ../tests/src/pause_resume.c \
  ../thpool.c \

ex_wait.parse: \
  ../tests/src/wait.c \
  ../thpool.c \

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC) -print-lib-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
