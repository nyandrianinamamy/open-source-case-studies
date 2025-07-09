/* Code based on a Stack Overflow answer;
   https://stackoverflow.com/questions/994593
   DO _NOT_ GO THERE BEFORE DOING THE EXERCISE, IT CONTAINS SPOILERS!
*/

#include <limits.h>
#include <stdio.h>

// Compute the integer log2 of val
int mylog2(int val) {
  if (val == 1) return 0;
  int ret = 0;
  while (val > 1) {
    val >>= 1;
    ret++;
  }
  return ret;
}

int main(void) {
  for (int i = 0; i < 20; i++)
    printf("%u -> %u\n", i, mylog2(i));
  putchar('\n');
  printf("%d -> %d\n", 100, mylog2(100));
  printf("%d -> %d\n", 1000, mylog2(1000));
  printf("%d -> %d\n", 10000, mylog2(10000));
  printf("%d -> %d\n", 1000000, mylog2(1000000));
  printf("%d -> %d\n", INT_MAX, mylog2(INT_MAX));
  printf("%d -> %d\n", INT_MAX+1, mylog2(INT_MAX+1));
  return 0;
}
