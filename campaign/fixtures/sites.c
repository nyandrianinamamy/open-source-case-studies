/* Two calls under a condition set by the macro SIDE. The analysis reaches
   f(2) with SIDE 0 and f(1) with SIDE 1, and the two runs give the same
   call site and statement number to these different calls. The digests of
   their ASTs differ, so the statement numbers of the two runs are not
   comparable and the calls must not be aligned. */
volatile int observable;
void f(int v) { observable = v; }
int main(void) {
  if (SIDE) f(1); else f(2);
  return 0;
}
