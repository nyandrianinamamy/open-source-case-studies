/* The macro SIDE sets the initial value of side, in an included header.
   The statements of the two runs are the same; the listing of the AST
   records the global declarations and their initial values too, so the
   digests differ and the calls are not aligned. */
#include "header.h"
volatile int observable;
void f(int v) { observable = v; }
int main(void) {
  if (side) f(1); else f(2);
  return 0;
}
