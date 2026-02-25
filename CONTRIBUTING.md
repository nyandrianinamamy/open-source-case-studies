## Adding a new case study

1. Create a new directory and copy the case study files inside it.
   If you have the choice between uncompressing an archive from a release, or
   cloning a Git repository, usually the release archive is preferred.
   It often contains some scripts such as `configure` (instead of just
   `configure.ac`), which are useful for versioning.
   If you copy a Git clone, remove the `.git` directory (we currently do not use
   submodules for case studies).
2. If possible, do some cleanup, removing excessively large files (e.g. test
   inputs, HTML documentation), unnecessary files (`.github`, `.travis.yml`,
   some binary files, etc). I recommend using `qdirstat` or a similar tool to
   quickly check if such files (especially large ones) remain.
3. If there is a `configure` script, consider running
   `frama-c-script configure [options]`. If helps disable some optional
   extensions. If you use any options (e.g. `--disable-readline`), consider
   documenting them by adding a `configure-for-oscs.txt` file or similar.
   Also, it may be useful to commit a generated `config.h` file, if such file
   exists, to allow users to reparse the sources without having to re-run
   build scripts. Also, it is often necessary to manually edit such files to
   remove external dependencies.
4. (Optional) Check if there is a Makefile and if typing `make` produces an
   executable file (if relevant). Consider writing/modifing a Makefile to
   add such a target if it does not exist.
5. Prepare the `.frama-c` folder. You can often copy an existing one
   (e.g. from `2048`) and adapt the `GNUmakefile` inside. Make sure the
   `path.mk` file inside it is a *symbolic link* to the root one, i.e.
   `../path.mk`.
6. Inside the `GNUmakefile`, add/modify `.parse` targets (lists of files to
   be parsed), and variables such as `FCFLAGS`, `EVAFLAGS`, etc.
7. Run `make` inside the `.frama-c` directory and adjust the analysis until
   it terminates succesfully (no parsing errors, no missing specifications,
   no recursive calls without assigns, etc).
8. Add all files to `.git` (the `.gitiginore` at the root directory should
   exclude unwanted files inside `.frama-c`).
9. Add an `OSCS-README.txt` file with four lines:
   - A short description of the use case;
   - An URL to its source repository;
   - A "tags" line (see `README.md`);
   - A "kind" line (see `README.md`).
10. Edit `.gitlab-ci.yml` to add the use case directory (copy-paste and adapt
    from existing examples) in alphabetical order.
11. Add the directory to the base `Makefile`, inside the `TARGETS` variable
    in alphabetical order.
12. Add a line to `README.md`, including the license (either in a
    `LICENSE`-like file in the case study directory, or some header that
    specifies it).
13. Run `./compute-summary.sh` and check that `summary.md` was modified, with
    an extra line for the newly-added directory.
14. Create a new branch (e.g. `new-<dir>`, or `add-<dir>`, where `<dir>` is the
    case study's directory) and commit to it. Push the branch to
    pub/open-source-case-studies.
