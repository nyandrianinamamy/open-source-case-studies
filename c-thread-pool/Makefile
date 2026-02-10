# This Makefile is NOT for running Frama-C, but for compiling the case study
# itself.

TARGETS:= \
  cThreadPool \
  api \
  conc_increment \
  no_work \
  nonzero_heap_stack \
  pause_resume \
  wait \

all: $(TARGETS)

cThreadPool: \
  example.c \
  thpool.c \

api: \
  tests/src/api.c \
  thpool.c \

conc_increment: \
  tests/src/conc_increment.c \
  thpool.c \

no_work: \
  tests/src/no_work.c \
  thpool.c \

nonzero_heap_stack: \
  tests/src/nonzero_heap_stack.c \
  thpool.c \

pause_resume: \
  tests/src/pause_resume.c \
  thpool.c \

wait: \
  tests/src/wait.c \
  thpool.c \

$(TARGETS):
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGETS)

.PHONY: clean
