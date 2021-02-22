# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC)-config -print-share-path)/analysis-scripts/prologue.mk
###############################################################################

# Edit below as needed. Suggested flags are optional.

MACHDEP = gcc_x86_64

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \

## General flags
FCFLAGS     += \
  -add-symbolic-path=..:. \
  -kernel-warn-key typing:implicit-function-declaration=abort \

## Eva-specific flags
EVAFLAGS    += \
  -eva-precision 3 \
  -eva-ignore-recursive-calls \

# Note: -eva-precision >3 (including 11) does not change anything

## GUI-only flags
FCGUIFLAGS += \

###############################################################################
# Filtered test cases:
# 00162.c - Frama-C does not yet parse 'void fooc(int [const 5]);'
# 00209.c - Frama-C does not yet parse 'int f1 (int (), int);'
# 00213.c - Clang reports: "C99 forbids conditional expressions with only one
#           void side"; also uses GNU statement expressions
# 00216.c - Frama-C does not support the GNU extension:
#           "Initialization of a flex array member"
# 00219.c - uses _Generic
SRCS=$(filter-out \
  ../00162.c \
  ../00209.c \
  ../00213.c \
  ../00216.c \
  ../00219.c \
  ,$(wildcard ../*.c))

## Analysis targets (suffixed with .eva)
TARGETS=$(addsuffix .eva,$(notdir $(basename $(SRCS))))

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites
define generate-parse-rule =
  $(notdir $(basename $(1))).parse: $(1)
endef

$(foreach s,$(SRCS),$(eval $(call generate-parse-rule,$(s))))

define print-stats =
$(shell grep alarms $(1)/stats.txt) $(shell grep warnings $(1)/stats.txt)
endef

###############################################################################
# The special target 'report' outputs the number of warnings and alarms
# reported by Eva, one line per source file.

report: all
	@$(foreach t,$(sort $(TARGETS)),\
	  echo "$(basename $(t)).c: $(call print-stats,$(t))";)

.PHONY: report

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC)-config -print-share-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
