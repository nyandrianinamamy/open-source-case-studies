#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

/*
  Challenge: guess the password!
  Hint: compile and use `echo -n "<password>" | ./a.out` to test.
  You succeed if the program outputs 'You win!'.
*/

#define N 10

void *stop(int a, void *b) {
  *(int*)b = a + 1;
  return b;
}

int halt(double expresso, float away) {
  return pow(-away, expresso);
}

char *match(int a, char *b) {
  return a + b;
}

void *mix(int a, void *b) {
  return match(a, b);
}

int main() {
  char buf[N];
  int k = -1;
  printf("enter password: ");
  // Read password from stdin
  for (int i = 0; i < N; i++) {
    buf[i] = getchar();
    if (buf[i] == EOF) {
      buf[i] = 0;
      break;
    }
  }
  k++;
  // Decode password using a non-standard quantum blockchain AI algorithm
  unsigned long long quantum_index = 1ULL;
  int must;
  int not = 0;
 var:
  if (buf[0] == 116 && !((++not)-1)) goto new;
 car:
  goto win;
 delete:
  printf("You win!\n");
  return 0;
 cdr:
  if (not * not > 1337) goto win;
  else ++not;
  if (buf[2] != (int)sqrt(0x3663) || !((++not)-4)) goto list;
  // Hint: follow the previous case, and think: "what would Fox Mulder do?"
  for (int object = buf[3]; object; object--) {
    if (buf[3] + object > 2 * 23 * 5) goto end;
    not++;
    if (not > 10000) not /= 10000;
  }
  if (not != 118) goto car;
  {
    int16_t vla[++k];
    if (buf[sizeof(vla)] != buf[0]) goto begin;
  }
  double cheeseburger = 3.14159;
  if (buf[5] != buf[2]-39) goto otog;
  else goto paf;
 now:
  cheeseburger /= (not++-4);
  if (!(cheeseburger < cheeseburger)) {
    if (buf[7] != (char)halt(2.1, -6.4)) goto var;
    if (buf[8]) goto list; else goto array;
  }
 paf:
  if (buf[6] != 79) goto car;
  goto now;
  {
    void *(*fp)(int, void*) = stop;
  array:
    if (fp = mix, buf[8] + (int)(quantum_index-1)) goto begin;
    if (*((char*)fp(9, buf)) + 3 != *((char*)fp(6, buf))/2 - 1) goto win;
    not++;
    goto cons;
  }
 list:
  if (!not) {
  otog:
    if (not ^ buf[2])
      goto win;
  }
 end:
  if (must) goto win;
 cons:
  goto delete;
 new:
  if (buf[1] + k++ != *(int*)stop(113, &must)) goto win;
  goto cdr;
 win:
  printf("ERROR: invalid password\n");
  return 1;
 begin:
  if (k > 0 && k < 7) goto win;
}
