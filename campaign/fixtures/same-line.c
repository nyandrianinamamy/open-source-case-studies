/* Two calls on one line. The macro SIDE sets the initial value of side,
   not the condition, so both runs parse the same statements: with SIDE 0
   the analysis reaches the call f(2) only, with SIDE 1 the call f(1) only.
   The two calls have one call site, line 10, and must not be aligned. */
volatile int observable;
int side = SIDE;
void f(int v) { observable = v; }

int main(void) {
  if (side) f(1); else f(2);
  return 0;
}
