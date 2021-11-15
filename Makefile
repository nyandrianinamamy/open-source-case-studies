.ONESHELL:

help::
	@echo "*** PREPARATION TARGETS (first-time user)"
	@echo "- 'make submodules': initialize the git submodules"
	@echo "- 'make framac' (optional): build and install a local Frama-C"
	@echo "   (alternatively, you can use a Frama-C installed in the PATH)"
	@echo "   Note: this target always forces a rebuild, and"
	@echo "         supplies -j automatically"
	@echo ""
	@echo "*** EXECUTION TARGETS"
	@echo "- 'make all': run all analyses"
	@echo "   Note: if you change the Frama-C version, you need to add -B"
	@echo "         (targets are not marked as dependent on Frama-C itself)"
	@echo "- 'make clean': clean all analyses"
	@echo ""
	@echo "*** USAGE WITH FRAMA-C INSTALLED IN THE PATH"
	@echo "- delete 'path.mk' or comment its lines"

# Note: if the user runs `make framac` before `make submodules`, the latter
# will fail.
submodules:
	@git submodule init
	git submodule update
	if ! grep '^build/$$' .git/modules/frama-c/info/exclude >/dev/null; then
	  echo "build/" >> .git/modules/frama-c/info/exclude;
	  echo "git ignoring 'build' directory in frama-c submodule";
	fi

framac: frama-c/build/bin/frama-c

# frama-c cannot depend on .git/.../something because when it is used as
# a submodule, it does not have a `.git` directory.
# also, such dependency would prevent usage with FRAMAC=path/to/other/framac
frama-c/build/bin/frama-c:
	@echo "Compiling and installing local Frama-C..."
	mkdir -p frama-c/build
	{
	  cd frama-c
	  echo "*** running autoconf..."
	  autoconf -f >/dev/null 2>/dev/null
	  echo "*** running configure..."
	  ./configure --prefix=`pwd`/build --quiet >/dev/null
	  $(MAKE) clean >/dev/null
	  echo "*** running make..."
	  $(MAKE) -j --quiet >/dev/null
	  echo "*** running make install..."
	  $(MAKE) install >/dev/null
	};
	echo "Local Frama-C (re-)installed."

TARGETS=\
  2048 \
  basic-cwe-examples \
  bench-moerman2018 \
  c-testsuite \
  cerberus \
  chrony \
  debie1 \
  genann \
  gzip124 \
  hiredis \
  icpc \
  ioccc \
  itc-benchmarks \
  jsmn \
  kgflags \
  khash \
  kilo \
  libmodbus \
  libspng \
  libyaml \
  microstrain \
  mini-gmp \
  miniz \
  monocypher \
  papabench \
  polarssl \
  qlz \
  safestringlib \
  semver \
  solitaire \
  tsvc \
  tweetnacl-usable \
  verisec \
  x509-parser \

help::
	@echo ""
	@echo "Known targets:"
	@echo "$(sort $(TARGETS))"

# A target for "fast" analyses, used to speed up testing
QUICK_TARGETS=$(filter-out polarssl gzip124 libmodbus monocypher chrony,$(TARGETS))

all: $(TARGETS)

summary:
	frama-c/share/analysis-scripts/summary.py

$(TARGETS):
	+$(MAKE) -C $@/.frama-c

quick: $(QUICK_TARGETS)

%.clean:
	$(MAKE) -C $*/.frama-c clean

clean: $(addsuffix .clean,$(TARGETS))

%.parse:
	$(MAKE) -C $*/.frama-c parse

parse: $(addsuffix .parse,$(TARGETS))

%.stats:
	$(MAKE) -C $*/.frama-c stats

stats: $(addsuffix .stats,$(TARGETS))

%.sarif:
	$(MAKE) -C $*/.frama-c sarif

sarif: $(addsuffix .sarif,$(TARGETS))

display-targets:
	@echo $(foreach target,$(TARGETS),\
	        $(addprefix $(target)/,\
	          $(shell $(MAKE) --quiet -C $(target)/.frama-c display-targets)))

.PHONY: $(TARGETS) frama-c/build/bin/frama-c clean-all help stats-all

# for continuous integration: runs all tests, then uses git status and
# git diff to check for unexpected differences
ci-tests: all stats-all
	git status --porcelain
	git diff --exit-code

ci-tests: export FCFLAGS=-value-verbose 0 -kernel-verbose 0
