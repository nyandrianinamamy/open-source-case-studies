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
  -I.. \

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
  ex_bitarray.eva \
  ex_doublylinkedlist.eva \
  ex_doublylinkedlist_6.eva \
  ex_graph.eva \
  ex_linkedlist.eva \
  ex_linkedlist_6.eva \
  ex_permutation.eva \
  ex_queue.eva \
  ex_queue_6.eva \
  ex_stack.eva \
  ex_stack_6.eva \
  ex_stringlib.eva \
  ex_timing.eva \
  # ex_fileutils.eva \

### Each target <t>.eva needs a rule <t>.parse with source files as prerequisites
ex_bitarray.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_bitarray.parse: \
  ../examples/bitarray_example.c \
  ../src/bitarray.c \

ex_doublylinkedlist.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_doublylinkedlist.eva: EVAFLAGS += -eva-precision 5
ex_doublylinkedlist.eva: EVAFLAGS += -main eva_main
ex_doublylinkedlist.parse: \
  ../examples/doublylinkedlist_example.c \
  ../src/dllist.c \
  fc_stubs.c \

# Target doublylinkedlist example with NUM_ELEMENTS=6 : no errors
ex_doublylinkedlist_6.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_doublylinkedlist_6.eva: EVAFLAGS += -main eva_main
ex_doublylinkedlist_6.eva: EVAFLAGS += -eva-precision 8
ex_doublylinkedlist_6.eva: EVAFLAGS += -eva-alloc-builtin fresh
ex_doublylinkedlist_6.parse: CPPFLAGS += -DNUM_ELEMENTS=6
ex_doublylinkedlist_6.parse: \
  ../examples/doublylinkedlist_example.c \
  ../src/dllist.c \
  fc_stubs.c \

# ex_fileutils.eva: EVAFLAGS += -eva-no-alloc-returns-null
# ex_fileutils.eva: EVAFLAGS += -eva-precision 7
# ex_fileutils.eva: EVAFLAGS += -main eva_main
# ex_fileutils.parse: \
#   ../examples/fileutils_example.c \
#   ../src/fileutils.c \
#   $(shell $(FRAMAC) -print-share-path)/libc/stdlib.c \

ex_graph.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_graph.eva: EVAFLAGS += -eva-precision 5
ex_graph.eva: EVAFLAGS += -main eva_main
ex_graph.eva: EVAFLAGS += -eva-unroll-recursive-calls 15
ex_graph.parse: \
  ../examples/graph_example.c \
  ../src/graph.c \
  fc_stubs.c \
  $(shell $(FRAMAC) -print-share-path)/libc/stdlib.c \
  $(shell $(FRAMAC) -print-share-path)/libc/string.c \

ex_linkedlist.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_linkedlist.eva: EVAFLAGS += -main eva_main
ex_linkedlist.eva: EVAFLAGS += -eva-precision 5
ex_linkedlist.parse: \
  ../examples/linkedlist_example.c \
  ../src/llist.c \
  fc_stubs.c \

# Target linkedlist example with NUM_ELEMENTS=6 : no errors
ex_linkedlist_6.eva: EVAFLAGS += -eva-alloc-builtin fresh
ex_linkedlist_6.eva: EVAFLAGS += -eva-precision 8
ex_linkedlist_6.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_linkedlist_6.eva: EVAFLAGS += -main eva_main
ex_linkedlist_6.parse: CPPFLAGS += -DNUM_ELEMENTS=6
ex_linkedlist_6.parse: \
  ../examples/doublylinkedlist_example.c \
  ../src/dllist.c \
  fc_stubs.c \

ex_permutation.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_permutation.eva: EVAFLAGS += -eva-precision 5
ex_permutation.parse: \
  ../examples/permutations_example.c \
  ../src/permutations.c \

ex_queue.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_queue.eva: EVAFLAGS += -main eva_main
ex_queue.eva: EVAFLAGS += -eva-precision 5
ex_queue.parse: \
  ../examples/queue_example.c \
  ../src/queue.c \
  fc_stubs.c \

# Target queue example with NUM_ELEMENTS=6 : no errors
ex_queue_6.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_queue_6.eva: EVAFLAGS += -main eva_main
ex_queue_6.eva: EVAFLAGS += -eva-alloc-builtin fresh
ex_queue_6.eva: EVAFLAGS += -eva-precision 8
ex_queue_6.parse: CPPFLAGS += -DNUM_ELEMENTS=6
ex_queue_6.parse: \
  ../examples/queue_example.c \
  ../src/queue.c \
  fc_stubs.c \

ex_stack.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_stack.eva: EVAFLAGS += -eva-precision 5
ex_stack.eva: EVAFLAGS += -main eva_main
ex_stack.parse: \
  ../examples/stack_example.c \
  ../src/stack.c \
  fc_stubs.c \

# Target stack example with NUM_ELEMENTS=6 : no errors
ex_stack_6.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_stack_6.eva: EVAFLAGS += -main eva_main
ex_stack_6.eva: EVAFLAGS += -eva-alloc-builtin fresh
ex_stack_6.eva: EVAFLAGS += -eva-precision 8
ex_stack_6.parse: CPPFLAGS += -DNUM_ELEMENTS=6
ex_stack_6.parse: \
  ../examples/queue_example.c \
  ../src/queue.c \
  fc_stubs.c \

ex_stringlib.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_stringlib.eva: EVAFLAGS += -eva-precision 8
ex_stringlib.eva: EVAFLAGS += -main eva_main
ex_stringlib.parse: \
  ../examples/stringlib_example.c \
  ../src/stringlib.c \
  fc_stubs.c \
  $(shell $(FRAMAC) -print-share-path)/libc/string.c \

ex_timing.eva: EVAFLAGS += -eva-no-alloc-returns-null
ex_timing.eva: EVAFLAGS += -eva-precision 5
ex_timing.eva: EVAFLAGS += -eva-plevel 1000000
ex_timing.parse: \
  ../examples/timing_example.c \

### Epilogue. Do not modify this block. #######################################
include $(shell $(FRAMAC) -print-lib-path)/analysis-scripts/epilogue.mk
###############################################################################

# optional, for OSCS
-include ../../Makefile.common
