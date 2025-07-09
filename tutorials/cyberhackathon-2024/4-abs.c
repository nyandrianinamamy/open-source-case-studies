#include <limits.h>

#ifdef __FRAMAC__
#include "__fc_builtin.h"
#endif

/*@
  requires x > INT_MIN;
  ensures \result >= 0;
*/
int myabs(int x) {
  if (x >= 0)
    return x;
  else
    return -x;
}

int main() {
  int input = Frama_C_interval(INT_MIN+1, INT_MAX);
  int r = myabs(input);
  return 0;
}
