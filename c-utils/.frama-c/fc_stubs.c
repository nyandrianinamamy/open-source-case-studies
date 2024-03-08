#include <string.h>
#include <stdlib.h>

#ifdef __FRAMAC__
# include "__fc_builtin.h"
int main(int, char **);
int eva_main() {
  int argc = Frama_C_interval(0, 1);
  char argv0[256];
  char *argv[2] = {argv0, 0};
  //@ loop unroll 2;
  for (int i = 0; i < argc; i++) {
    Frama_C_make_unknown(argv[i], 255);
    argv[i][255] = 0;
  }
  return main(argc, argv);
}
#endif // __FRAMAC__
