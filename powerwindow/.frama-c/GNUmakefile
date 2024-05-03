# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC)-config -print-lib-path)/analysis-scripts/prologue.mk
###############################################################################

# Edit below as needed. Suggested flags are optional.

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \

## General flags
FCFLAGS     += \
  -add-symbolic-path=..:. \
  -kernel-warn-key annot:missing-spec=abort \
  -kernel-warn-key typing:implicit-function-declaration=abort \

## Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \
  -eva-auto-loop-unroll 368 \

## GUI-only flags
FCGUIFLAGS += \

## Analysis targets (suffixed with .eva)
TARGETS = powerwindow.eva

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites
powerwindow.parse: \
  ../powerwindow.c \
  ../powerwindow_const_params.c \
  ../powerwindow_controlexclusion.c \
  ../powerwindow_debounce.c \
  ../powerwindow_inputs.c \
  ../powerwindow_powerwindow_control.c \
  ../powerwindow_PW_Control_DRV.c \
  ../powerwindow_PW_Control_PSG_BackL.c \
  ../powerwindow_PW_Control_PSG_BackR.c \
  ../powerwindow_PW_Control_PSG_Front.c \
  ../wcclib.c \

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC)-config -print-lib-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
