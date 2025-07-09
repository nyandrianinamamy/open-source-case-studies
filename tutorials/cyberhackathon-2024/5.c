#include <stdio.h>
#include <string.h>

#define N 16

int main() {
  char buf[N];
  printf("Enter your name:\n");
  fgets(buf, N, stdin);
  printf("Name: %s (length %zd)\n", buf, strlen(buf));
  return 0;
}
