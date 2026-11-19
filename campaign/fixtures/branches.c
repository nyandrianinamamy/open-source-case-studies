/* Two calls of one text on one line. The analysis reaches the second call
   with SIDE 0 and the first with SIDE 1. The two runs give the same
   statement numbers, lines and texts to their statements; the listing of
   the AST records the columns of the calls too, so the digests differ and
   the calls are not aligned. */
volatile int observable;
void f(int v) { observable = v; }
int main(void) {
  if (SIDE) f(1); else f(1);
  return 0;
}
