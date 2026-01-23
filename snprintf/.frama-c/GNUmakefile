# Makefile template for Frama-C/Eva case studies.
# For details and usage information, see the Frama-C User Manual.

### Prologue. Do not modify this block. #######################################
-include path.mk
FRAMAC ?= frama-c
include $(shell $(FRAMAC) -print-lib-path)/analysis-scripts/prologue.mk
###############################################################################

# Edit below as needed. Suggested flags are optional.

MACHDEP = x86_64

## Preprocessing flags (for -cpp-extra-args)
CPPFLAGS    += \
  -I../include \

## Other preprocessing and parsing flags (e.g. -cpp-extra-args-per-file)
PARSEFLAGS    += \

## General flags
FCFLAGS     += \
  -add-symbolic-path=..:. \
  -kernel-warn-key annot:missing-spec=abort \
  -kernel-warn-key typing:implicit-function-declaration=abort \

## Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \
  -eva-warn-key libc:unsupported-spec=abort \
  -eva-warn-key recursion=abort \
  -eva-precision 5 \

# Note: if the code has recursive calls, manually review them, add assigns as
# needed, and remove the line '-eva-warn-key recursion=abort' above

## WP-specific flags
WPFLAGS    += \

## GUI-only flags
FCGUIFLAGS += \

## Analysis targets (suffixed with .eva)
TARGETS = \
  tests-snprintf1.eva \
  tests-snprintf2.eva \
  tests-snprintf3.eva \
  tests-snprintf4.eva \
  tests-snprintf5.eva \
  tests-snprintf6.eva \
  tests-snprintf7.eva \
  tests-snprintf8.eva \
  tests-snprintf9.eva \
  tests-snprintf10.eva \
  tests-snprintf11.eva \
  tests-snprintf12.eva \
  tests-snprintf13.eva \
  tests-snprintf14.eva \
  tests-snprintf15.eva \
  tests-snprintf16.eva \
  tests-snprintf17.eva \
  tests-snprintf18.eva \
  tests-snprintf19.eva \
  tests-snprintf20.eva \
  tests-snprintf21.eva \
  tests-snprintf22.eva \
  tests-snprintf23.eva \
  tests-snprintf24.eva \
  tests-snprintf25.eva \
  tests-snprintf26.eva \
  tests-snprintf27.eva \
  tests-snprintf28.eva \
  tests-snprintf29.eva \
  tests-snprintf30.eva \
  tests-snprintf31.eva \
  tests-snprintf32.eva \
  tests-snprintf33.eva \
  tests-snprintf34.eva \
  tests-snprintf35.eva \
  tests-snprintf36.eva \
  tests-snprintf37.eva \
  tests-snprintf38.eva \
  tests-snprintf39.eva \
  tests-snprintf40.eva \
  tests-snprintf41.eva \
  tests-snprintf42.eva \
  tests-snprintf43.eva \
  tests-snprintf44.eva \
  tests-snprintf45.eva \
  tests-snprintf46.eva \
  tests-snprintf47.eva \
  tests-snprintf48.eva \
  tests-snprintf49.eva \
  tests-snprintf50.eva \
  tests-snprintf51.eva \
  tests-snprintf52.eva \
  tests-snprintf53.eva \
  tests-snprintf54.eva \
  tests-snprintf55.eva \
  tests-snprintf56.eva \
  tests-snprintf57.eva \
  tests-snprintf58.eva \
  tests-snprintf59.eva \
  tests-snprintf60.eva \
  tests-snprintf61.eva \
  tests-snprintf62.eva \
  tests-snprintf63.eva \
  tests-snprintf64.eva \
  tests-snprintf65.eva \
  tests-snprintf66.eva \

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites

SRCS := \
  ../src/snprintf.c \
  ../src/tests-snprintf.c \
  $(shell $(FRAMAC) -print-share-path)/libc/string.c

tests-snprintf1.parse: $(SRCS)
tests-snprintf1.parse: CPPFLAGS += -DCUR_TEST=1

tests-snprintf2.parse: $(SRCS)
tests-snprintf2.parse: CPPFLAGS += -DCUR_TEST=2

tests-snprintf3.parse: $(SRCS)
tests-snprintf3.parse: CPPFLAGS += -DCUR_TEST=3

tests-snprintf4.parse: $(SRCS)
tests-snprintf4.parse: CPPFLAGS += -DCUR_TEST=4

tests-snprintf5.parse: $(SRCS)
tests-snprintf5.parse: CPPFLAGS += -DCUR_TEST=5

tests-snprintf6.parse: $(SRCS)
tests-snprintf6.parse: CPPFLAGS += -DCUR_TEST=6

tests-snprintf7.parse: $(SRCS)
tests-snprintf7.parse: CPPFLAGS += -DCUR_TEST=7

tests-snprintf8.parse: $(SRCS)
tests-snprintf8.parse: CPPFLAGS += -DCUR_TEST=8

tests-snprintf9.parse: $(SRCS)
tests-snprintf9.parse: CPPFLAGS += -DCUR_TEST=9

tests-snprintf10.parse: $(SRCS)
tests-snprintf10.parse: CPPFLAGS += -DCUR_TEST=10

tests-snprintf11.parse: $(SRCS)
tests-snprintf11.parse: CPPFLAGS += -DCUR_TEST=11

tests-snprintf12.parse: $(SRCS)
tests-snprintf12.parse: CPPFLAGS += -DCUR_TEST=12

tests-snprintf13.parse: $(SRCS)
tests-snprintf13.parse: CPPFLAGS += -DCUR_TEST=13

tests-snprintf14.parse: $(SRCS)
tests-snprintf14.parse: CPPFLAGS += -DCUR_TEST=14

tests-snprintf15.parse: $(SRCS)
tests-snprintf15.parse: CPPFLAGS += -DCUR_TEST=15

tests-snprintf16.parse: $(SRCS)
tests-snprintf16.parse: CPPFLAGS += -DCUR_TEST=16

tests-snprintf17.parse: $(SRCS)
tests-snprintf17.parse: CPPFLAGS += -DCUR_TEST=17

tests-snprintf18.parse: $(SRCS)
tests-snprintf18.parse: CPPFLAGS += -DCUR_TEST=18

tests-snprintf19.parse: $(SRCS)
tests-snprintf19.parse: CPPFLAGS += -DCUR_TEST=19

tests-snprintf20.parse: $(SRCS)
tests-snprintf20.parse: CPPFLAGS += -DCUR_TEST=20

tests-snprintf21.parse: $(SRCS)
tests-snprintf21.parse: CPPFLAGS += -DCUR_TEST=21

tests-snprintf22.parse: $(SRCS)
tests-snprintf22.parse: CPPFLAGS += -DCUR_TEST=22

tests-snprintf23.parse: $(SRCS)
tests-snprintf23.parse: CPPFLAGS += -DCUR_TEST=23

tests-snprintf24.parse: $(SRCS)
tests-snprintf24.parse: CPPFLAGS += -DCUR_TEST=24

tests-snprintf25.parse: $(SRCS)
tests-snprintf25.parse: CPPFLAGS += -DCUR_TEST=25

tests-snprintf26.parse: $(SRCS)
tests-snprintf26.parse: CPPFLAGS += -DCUR_TEST=26

tests-snprintf27.parse: $(SRCS)
tests-snprintf27.parse: CPPFLAGS += -DCUR_TEST=27

tests-snprintf28.parse: $(SRCS)
tests-snprintf28.parse: CPPFLAGS += -DCUR_TEST=28

tests-snprintf29.parse: $(SRCS)
tests-snprintf29.parse: CPPFLAGS += -DCUR_TEST=29

tests-snprintf30.parse: $(SRCS)
tests-snprintf30.parse: CPPFLAGS += -DCUR_TEST=30

tests-snprintf31.parse: $(SRCS)
tests-snprintf31.parse: CPPFLAGS += -DCUR_TEST=31

tests-snprintf32.parse: $(SRCS)
tests-snprintf32.parse: CPPFLAGS += -DCUR_TEST=32

tests-snprintf33.parse: $(SRCS)
tests-snprintf33.parse: CPPFLAGS += -DCUR_TEST=33

tests-snprintf34.parse: $(SRCS)
tests-snprintf34.parse: CPPFLAGS += -DCUR_TEST=34

tests-snprintf35.parse: $(SRCS)
tests-snprintf35.parse: CPPFLAGS += -DCUR_TEST=35

tests-snprintf36.parse: $(SRCS)
tests-snprintf36.parse: CPPFLAGS += -DCUR_TEST=36

tests-snprintf37.parse: $(SRCS)
tests-snprintf37.parse: CPPFLAGS += -DCUR_TEST=37

tests-snprintf38.parse: $(SRCS)
tests-snprintf38.parse: CPPFLAGS += -DCUR_TEST=38

tests-snprintf39.parse: $(SRCS)
tests-snprintf39.parse: CPPFLAGS += -DCUR_TEST=39

tests-snprintf40.parse: $(SRCS)
tests-snprintf40.parse: CPPFLAGS += -DCUR_TEST=40

tests-snprintf41.parse: $(SRCS)
tests-snprintf41.parse: CPPFLAGS += -DCUR_TEST=41

tests-snprintf42.parse: $(SRCS)
tests-snprintf42.parse: CPPFLAGS += -DCUR_TEST=42

tests-snprintf43.parse: $(SRCS)
tests-snprintf43.parse: CPPFLAGS += -DCUR_TEST=43

tests-snprintf44.parse: $(SRCS)
tests-snprintf44.parse: CPPFLAGS += -DCUR_TEST=44

tests-snprintf45.parse: $(SRCS)
tests-snprintf45.parse: CPPFLAGS += -DCUR_TEST=45

tests-snprintf46.parse: $(SRCS)
tests-snprintf46.parse: CPPFLAGS += -DCUR_TEST=46

tests-snprintf47.parse: $(SRCS)
tests-snprintf47.parse: CPPFLAGS += -DCUR_TEST=47

tests-snprintf48.parse: $(SRCS)
tests-snprintf48.parse: CPPFLAGS += -DCUR_TEST=48

tests-snprintf49.parse: $(SRCS)
tests-snprintf49.parse: CPPFLAGS += -DCUR_TEST=49

tests-snprintf50.parse: $(SRCS)
tests-snprintf50.parse: CPPFLAGS += -DCUR_TEST=50

tests-snprintf51.parse: $(SRCS)
tests-snprintf51.parse: CPPFLAGS += -DCUR_TEST=51

tests-snprintf52.parse: $(SRCS)
tests-snprintf52.parse: CPPFLAGS += -DCUR_TEST=52

tests-snprintf53.parse: $(SRCS)
tests-snprintf53.parse: CPPFLAGS += -DCUR_TEST=53

tests-snprintf54.parse: $(SRCS)
tests-snprintf54.parse: CPPFLAGS += -DCUR_TEST=54

tests-snprintf55.parse: $(SRCS)
tests-snprintf55.parse: CPPFLAGS += -DCUR_TEST=55

tests-snprintf56.parse: $(SRCS)
tests-snprintf56.parse: CPPFLAGS += -DCUR_TEST=56

tests-snprintf57.parse: $(SRCS)
tests-snprintf57.parse: CPPFLAGS += -DCUR_TEST=57

tests-snprintf58.parse: $(SRCS)
tests-snprintf58.parse: CPPFLAGS += -DCUR_TEST=58

tests-snprintf59.parse: $(SRCS)
tests-snprintf59.parse: CPPFLAGS += -DCUR_TEST=59

tests-snprintf60.parse: $(SRCS)
tests-snprintf60.parse: CPPFLAGS += -DCUR_TEST=60

tests-snprintf61.parse: $(SRCS)
tests-snprintf61.parse: CPPFLAGS += -DCUR_TEST=61

tests-snprintf62.parse: $(SRCS)
tests-snprintf62.parse: CPPFLAGS += -DCUR_TEST=62

tests-snprintf63.parse: $(SRCS)
tests-snprintf63.parse: CPPFLAGS += -DCUR_TEST=63

tests-snprintf64.parse: $(SRCS)
tests-snprintf64.parse: CPPFLAGS += -DCUR_TEST=64

tests-snprintf65.parse: $(SRCS)
tests-snprintf65.parse: CPPFLAGS += -DCUR_TEST=65

tests-snprintf66.parse: $(SRCS)
tests-snprintf66.parse: CPPFLAGS += -DCUR_TEST=66

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC) -print-lib-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
