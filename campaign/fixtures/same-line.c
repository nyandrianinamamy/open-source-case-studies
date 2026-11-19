/* Two calls on one line. With the initial state of the program, side is 0
   and the analysis reaches the call f(2) only; with -lib-entry, side may
   hold any value and it reaches f(1) too. The two runs parse the same
   program, so their statement numbers are comparable: the calls f(2)
   align, and the call f(1), on the same line and call site, is unmatched,
   not aligned with f(2). */
volatile int observable;
int side = 0;
void f(int v) { observable = v; }

int main(void) {
  if (side) f(1); else f(2);
  return 0;
}
