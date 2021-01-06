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

## Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \

## GUI-only flags
FCGUIFLAGS += \

## Analysis targets (suffixed with .eva)
TARGETS = \
2020_burton_prog.eva \
2020_giles_prog.eva \
2020_kurdyukov1_prog.eva \
2020_kurdyukov1_prog_extra.eva \
2020_kurdyukov1_prog_orig.eva \
2020_kurdyukov2_prog_ppm.eva \
2020_kurdyukov3_prog.eva \
2020_kurdyukov3_prog_extra.eva \
2020_kurdyukov3_prog_orig.eva \
2020_kurdyukov4_prog.eva \
2020_otterness_prog.eva \

#### The folowing cases are not currently handled by Frama-C;
#### See comments in .parse lines

NOT_HANDLED=\
2020_carlini_prog.eva \
2020_endoh1_prog.eva \
2020_endoh1_prog_orig.eva \
2020_endoh2_prog.eva \
2020_endoh3_clock.eva \
2020_endoh3_prog.eva \
2020_endoh3_prog_alt.eva \
2020_ferguson1_termcaps.eva \
2020_ferguson1_prog_3.eva \
2020_ferguson1_prog.eva \
2020_ferguson1_prog_2.eva \
2020_ferguson1_prog_alt.eva \
2020_ferguson1_prog_3-j.eva \
2020_ferguson2_prog.eva \
2020_ferguson2_recode.eva \
2020_kurdyukov2_prog.eva \
2020_kurdyukov2_prog_png.eva \
2020_kurdyukov4_rand.eva \
2020_tsoj_prog.eva \
2020_yang_prog.eva \

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites

2020_burton_prog.parse: ../2020/burton/prog.c
2020_burton_prog.parse: FCFLAGS += -json-compilation-database ../2020/burton \

#2020_carlini_prog.parse: ../2020/carlini/prog.c #  missing spec for scanf with non-static format argument
#2020_carlini_prog.parse: FCFLAGS += -json-compilation-database ../2020/carlini \

#2020_endoh1_prog.parse: ../2020/endoh1/prog.c # requires <ncurses.h>

#2020_endoh1_prog_orig.parse: ../2020/endoh1/prog_orig.c # requires <ncurses.h>

#2020_endoh2_prog.parse: ../2020/endoh2/prog.c # requires <complex.h>

#2020_endoh3_clock.parse: ../2020/endoh3/clock.c # parsing issue with comment/slash

#2020_endoh3_prog.parse: ../2020/endoh3/prog.c # parsing issue with comment/slash

#2020_endoh3_prog_alt.parse: ../2020/endoh3/prog_alt.c # parsing issue with comment/slash

#2020_ferguson1_termcaps.parse: ../2020/ferguson1/termcaps.c # requires <curses.h>

#2020_ferguson1_prog_3.parse: ../2020/ferguson1/prog.3.c # requires <curses.h>

#2020_ferguson1_prog.parse: ../2020/ferguson1/prog.c # requires <curses.h>

#2020_ferguson1_prog_2.parse: ../2020/ferguson1/prog.2.c # requires <curses.h>

#2020_ferguson1_prog_alt.parse: ../2020/ferguson1/prog.alt.c # requires <curses.h>

#2020_ferguson1_prog_3-j.parse: ../2020/ferguson1/prog.3-j.c # requires <curses.h>

#2020_ferguson2_prog.parse: ../2020/ferguson2/prog.c # missing spec for stdio.h's getdelim

#2020_ferguson2_recode.parse: ../2020/ferguson2/recode.c # missing spec for stdio.h's getdelim

2020_giles_prog.parse: ../2020/giles/prog.c

2020_kurdyukov1_prog.parse: ../2020/kurdyukov1/prog.c

2020_kurdyukov1_prog_extra.parse: ../2020/kurdyukov1/prog.extra.c

2020_kurdyukov1_prog_orig.parse: ../2020/kurdyukov1/prog.orig.c

2020_kurdyukov2_prog_ppm.parse: ../2020/kurdyukov2/prog.ppm.c

#2020_kurdyukov2_prog.parse: ../2020/kurdyukov2/prog.c # requires <jpeglib.h>

#2020_kurdyukov2_prog_png.parse: ../2020/kurdyukov2/prog.png.c # requires <png.h>

2020_kurdyukov3_prog.parse: ../2020/kurdyukov3/prog.c

2020_kurdyukov3_prog_extra.parse: ../2020/kurdyukov3/prog.extra.c

2020_kurdyukov3_prog_orig.parse: ../2020/kurdyukov3/prog.orig.c

2020_kurdyukov4_prog.parse: ../2020/kurdyukov4/prog.c

#2020_kurdyukov4_rand.parse: ../2020/kurdyukov4/rand.c # missing spec for stdlib.h's memmem

2020_otterness_prog.parse: ../2020/otterness/prog.c

#2020_tsoj_prog.parse: ../2020/tsoj/prog.c # missing macro TIOCGWINSZ (ioctl)

#2020_yang_prog.parse: ../2020/yang/prog.c # missing spec for printf with non-static format argument

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC)-config -print-share-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
