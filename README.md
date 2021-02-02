![Pipeline status badge](https://git.frama-c.com/pub/open-source-case-studies/badges/master/pipeline.svg)

Open source case studies for Frama-C
====================================

This repository is a collection of open source C codes to be used with
[Frama-C](http://frama-c.com), in particular with the Eva
(Evolved Value Analysis) plug-in.

Most directories contain open-source code that constitutes a "case study".
A few contain sets of tests, benchmarks or tutorials.


# Requirements

- GNU Make >= 4.0;
- (optional, for some scripts) Python >= 3.6.

# Basic usage

- (required once) `make submodules`: initializes the local Frama-C submodule;
- (required once) `make framac`: prepares a git submodule with a clone
  of the public git of Frama-C, compiles it and installs it locally
  (in `frama-c/build/bin`);
- `cd` to one of the case studies;
  We recommend `2048` for a short and fast analysis, or `debie1` for
  a finalized analysis.
- Run `make` to parse and run Eva on the predefined targets.

## Makefile targets

The scripts provided with Frama-C create several Makefile targets,
according to the intended usage. The main ones are:

- `help`: lists the base targets
- For each base target `t`, the following targets are generated:
  - `t.parse`: parse the sources;
  - `t.eva`: run Eva;
  - `t.eva.gui`: open the GUI.

Each target depends on the previous one: running `t.eva.gui` will
automatically run `t.eva` if required; the same for `t.parse`.

Other generated targets:

- `t.parse.gui`: open the GUI with the result of the parsing, *without* running
  Eva. Mostly useful in conjunction with other plug-ins.
- `t.stats`: print time/memory usage.

### Remarks

- The output of `t.eva` is verbose, but you can ignore it;
  the important information (warnings and alarms) can be inspected via the GUI.
- The result of each analysis is stored in a directory containing the full logs
  and Frama-C save files; successive runs are copied into timestamped
  directories, to allow comparing them (e.g. via `meld`);
- To try other parametrizations, simply edit variables
  `CPPFLAGS/FCFLAGS/EVAFLAGS` in `GNUmakefile` and re-run `make`.
- Technical remark: the default file used by GNU Make is `GNUmakefile`,
  if it exists.
  We use this to avoid renaming the original Makefile, if any. It also means
  that, if you want to *compile* the code using its Makefile, you have to
  explicitly name it (e.g. `make -f Makefile`).


# Notes

## Source code modifications

Only minor modifications were performed on each of these case studies:

- File `GNUmakefile` is added to each case study, with Frama-C/Eva-specific
  rules for parsing and running the analysis;
- When necessary, syntactic modifications were performed to ensure better
  C99-compliance and/or the inclusion of stubs to allow Frama-C to parse the
  files;
- In some cases, an `eva_main` function was added to provide a better initial
  context for the analysis;
- When recursive calls are present, the functions containing them need to be
  replaced with specifications;
- Some ACSL annotations were added to the sources
  (to illustrate their usage, or to improve the analysis);
- Some unnecessary files for the analysis (e.g. documentation, project setups
  for IDEs, non-code resources) were removed.

## Rationale

The main objectives of these files are:

1. Non-regression tests;
2. Benchmarking;
3. Practical examples.

Therefore, some of the code bases are voluntarily parametrized with
suboptimal parameters, for non-regression testing. Some code bases undergo
partial, progressive improvements.
Only a few constitute "finalized" case studies.

# Contributions

If you know of other open source code bases where Frama-C/Eva produces
interesting results, please contribute with pull requests including the
sources and the `GNUmakefile` that you have devised to run Frama-C.

On the other hand, if you have some interesting open-source C software
(ideally, C99-compatible) that you are unable to parse and/or run with
Frama-C/Eva, consider creating an issue in this repository¹
with the description of the problem you are facing (e.g. missing/incompatible
declarations in the Frama-C libc, problems when preprocessing/parsing the
code, constructs unsupported by Eva, etc).
Ideally, create a (WIP) pull request with the sources in a new directory,
ready to be prepared for the case study.

¹ *Note*: direct account creation is disabled in Frama-C's Gitlab; linking
  a Github account is always possible.


# License

License files are kept in each directory where they were originally found,
when available. We also summarize the license of each directory below.

- `2048`: MIT
- `basic-cwe-examples`: see `LICENSE`
- `bench-moerman2018`: MIT
- `chrony`: GPL
- `debie1`: distribution and use authorized by Patria Aviation Oy,
            Space Systems Finland Ltd. and Tidorum Ltd, see `README.txt`
            and `terms_of_use-2014-05.pdf`
- `gzip124`: GPL
- `hiredis`: Redis license (BSD-style), see `COPYING`
- `icpc`: Unlicense
- `itc-benchmarks`: BSD 2-clause, see `COPYING`
- `jsmn`: MIT
- `kgflags`: MIT, see `LICENSE`
- `khash`: MIT
- `kilo`: BSD 2-clause "Simplified"
          (see https://github.com/antirez/kilo/blob/master/LICENSE)
- `libmodbus`: LGPL
- `libspng`: BSD 2-clause, see `LICENSE`
- `libyaml`: MIT, see `License`
- `mibench`: several (see `LICENSE` file inside each subdirectory)
- `mini-gmp`:  LGPL or GPL
- `miniz`:  MIT
- `microstrain`: GPL and others, see `LICENSE`
- `monocypher`: see `README`
- `papabench`: GPL
- `polarssl`: GPL
- `qlz`: GPL
- `safestringlib`: MIT
- `semver`: MIT
- `solitaire`: public domain (see `solitaire.c`)
- `tweetnacl-usable`: public domain (see `LICENSE.txt`)
- `x509-parser` : GPLv2 / BSD (see `LICENSE`)
