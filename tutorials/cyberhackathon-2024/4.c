/* Code based on a Stack Overflow answer;
   https://stackoverflow.com/questions/994593
   DO _NOT_ GO THERE BEFORE DOING THE EXERCISE, IT CONTAINS SPOILERS!
*/

#include <limits.h>

#ifdef __FRAMAC__
#include "__fc_builtin.h"
#endif

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
  int v = <TODO>;
  int r = mylog2(v);
  return 0;
}
