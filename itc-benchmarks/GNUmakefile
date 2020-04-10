# TEMPLATE FOR MAKEFILE TO USE IN FRAMA-C/EVA CASE STUDIES

# DO NOT EDIT THE LINES BETWEEN THE '#'S

###############################################################################
# Improves analysis time, at the cost of extra memory usage
export FRAMA_C_MEMORY_FOOTPRINT = 8
#
# frama-c-path.mk contains variables which are specific to each
# user and should not be versioned, such as the path to the
# frama-c binaries (e.g. FRAMAC and FRAMAC_GUI).
# It is an optional include, unnecessary if frama-c is in the PATH
-include frama-c-path.mk
#
# FRAMAC_CONFIG is defined in frama-c-path.mk when it is included, so the
# line below will be safely ignored if this is the case
FRAMAC_CONFIG ?= frama-c-config
#
# frama-c.mk contains the main rules and targets
-include $(shell $(FRAMAC_CONFIG) -print-share-path)/analysis-scripts/frama-c.mk
#
###############################################################################

# EDIT VARIABLES AND TARGETS BELOW AS NEEDED
# The flags below are only suggestions to use with Eva, and can be removed

# (Optional) preprocessing flags, usually handled by -json-compilation-database
CPPFLAGS    += -Iinclude -includefc_stubs.h

# (Optional) Frama-C general flags (parsing and kernel)
FCFLAGS     += \
  -kernel-warn-key annot:missing-spec=abort \
  -kernel-warn-key typing:implicit-function-declaration=abort \
  -warn-signed-downcast \
  -warn-unsigned-downcast \
  -warn-unsigned-overflow \

# (Optional) Eva-specific flags
EVAFLAGS    += \
  -eva-warn-key builtins:missing-spec=abort \
  -eva-no-alloc-returns-null \
  -eva-mlevel 10 \
  -main eva_main \
  -eva-precision 3 \
  -eva-builtin titcb_pow:Frama_C_pow \

# -eva-precision 3 reduces 1 unknown w.r.t. -eva-precision 2

SUBDIR_SRCS=\
main.c \
bit_shift.c \
buffer_overrun_dynamic.c \
buffer_underrun_dynamic.c \
data_lost.c \
data_overflow.c \
data_underflow.c \
double_free.c \
endless_loop.c \
free_nondynamic_allocated_memory.c \
invalid_memory_access.c \
littlemem_st.c \
memory_allocation_failure.c \
not_return.c \
null_pointer.c \
overrun_st.c \
pow_related_errors.c \
ptr_subtraction.c \
return_local.c \
sign_conv.c \
st_underrun.c \
underrun_st.c \
uninit_memory_access.c \
uninit_pointer.c \
uninit_var.c \
zero_division.c \


# (MANDATORY) Name of the main target
MAIN_TARGET := 01_w_Defects

# Add other targets if needed
TARGETS = $(MAIN_TARGET).eva 02_wo_Defects.eva

# Default target
all: $(TARGETS)

# NOTE: string.c is required due to the usage of strdup() in some tests,
# and also to avoid loss of precision when strcpy() is used.
# Both are related to tests in st_underrun.c

01_w_Defects.parse: \
fc_stubs.c \
$(shell $(FRAMAC_CONFIG) -print-share-path)/libc/stdio.c \
$(shell $(FRAMAC_CONFIG) -print-share-path)/libc/string.c \
$(foreach file,$(SUBDIR_SRCS),$(wildcard 01_w_Defects/$(file))) \

02_wo_Defects.parse: \
fc_stubs.c \
$(shell $(FRAMAC_CONFIG) -print-share-path)/libc/stdio.c \
$(shell $(FRAMAC_CONFIG) -print-share-path)/libc/string.c \
$(foreach file,$(SUBDIR_SRCS),$(wildcard 02_wo_Defects/$(file))) \

# The following targets are optional and provided for convenience only
parse: $(TARGETS:%.eva=%.parse)
gui: $(MAIN_TARGET).eva.gui

stats: $(TARGETS:%.eva=%.parse) $(TARGETS)
	../show_stats.sh "$(notdir $(CURDIR))" $^

# optional, for OSCS
-include ../Makefile.common

