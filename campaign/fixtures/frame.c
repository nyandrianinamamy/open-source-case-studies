/* Example run of issue #3 of nyandrianinamamy/frama-c: with memexec, the
   second call to get is a hit, and the state before "r = 0;" in get misses
   the value 5 of r, which the match of the cache entry does not check. */
#include "__fc_builtin.h"
int t[10];
int g;
int r;

int get(int i) {
  int v = t[i];
  r = 0;
  return v + g;
}

void main(void) {
  int a, b;
  g = 1;
  r = 3;
  a = get(Frama_C_interval(0, 10));
  r = 5;
  b = get(Frama_C_interval(0, 10));
}
