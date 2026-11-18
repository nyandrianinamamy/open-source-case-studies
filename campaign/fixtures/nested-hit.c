/* A call that is a hit with caching enabled and analysed with caching
   disabled: the second call to outer. Analysed, it makes two nested calls
   to leaf, which have no counterpart in the run where it is a hit. */
int leaf(int x) {
  return x + 1;
}

int outer(int x) {
  return leaf(x) + leaf(x + 1);
}

int main(void) {
  int a = outer(1);
  int b = outer(1);
  return a + b;
}
