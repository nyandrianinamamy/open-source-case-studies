# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC)-config -print-lib-path)/analysis-scripts/prologue.mk
###############################################################################

# Edit below as needed. Suggested flags are optional.

MACHDEP = x86_32

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \
  -include$(shell $(FRAMAC)-config -print-share-path)/libc/string.h \
  -DSTDC_HEADERS=1 \
  -DHAVE_UNISTD_H=1 \
  -DDIRENT=1 \
  -DNO_UTIME=1 \
  -I$(shell $(FRAMAC)-config -print-share-path)/libc \
  -I$(DIR) \

## General flags
FCFLAGS  += \
  -add-symbolic-path=..:. \
  -nonterm-ignore do_exit \
  -main eva_main \

## Eva-specific flags
EVAFLAGS += \
  -eva-slevel 2 \
  -eva-no-alloc-returns-null \

# Comparison with other parametrizations
# Baseline: -eva-no-alloc-returns-null -eva-slevel 2: time 120s
# -eva-slevel 3: time 511s, -0 alarms
# -eva-domains equality: time 201s, -12 alarms
# -eva-domains gauges: time 351s, -4 alarms
# -eva-domains equality,gauges: time 491s, -17 alarms

## GUI-only flags
FCGUIFLAGS += \
## Analysis targets (suffixed with .eva)
TARGETS = gzip124.eva

gzip124.parse: \
  $(shell $(FRAMAC)-config -print-share-path)/libc/stdlib.c \
  fc_stubs.c \
  ../bits.c \
  ../crypt.c \
  ../deflate.c \
  ../getopt.c \
  ../gzip.c \
  ../inflate.c \
  ../lzw.c \
  ../trees.c \
  ../unlzh.c \
  ../unlzw.c \
  ../unpack.c \
  ../unzip.c \
  ../util.c \
  ../zip.c \

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC)-config -print-lib-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
