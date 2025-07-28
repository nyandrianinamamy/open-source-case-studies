Go game
https://ftp.gnu.org/gnu/gnugo/
NO_DYN_ALLOC, HAS_RECURSION, NO_FLOAT
executable

- matchpat(): You can remove 1 alarm by defining `_FC_ACTIVE_LONG_PROOF`
  (referenced in matchpat.c) in CPPFLAGS
- endgame(): This function doesn't check the return value of getij() before
  using i and j
- fioe(): This function can read a value outside an array
