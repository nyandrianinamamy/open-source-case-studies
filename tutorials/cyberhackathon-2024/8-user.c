#include "8.h"

void user_ok(void) {
  struct file *f = createf("bla");
  writef(f, "hello world", 12);
  closef(f);
  openf(f, READ);
  seekf(f, 6);
  char buf[12];
  readf(f, buf, 6);
  printf("read: %s\n", buf);
}

void user_bad1(void) {
  writef(NULL, NULL, -1);
}

void user_bad2(void) {
  char buf[10];
  readf(passwd, buf, 10);
}

void user_bad3(void) {
  struct file *f = 0;
  readf(f, "a", 2);
}

void user_bad4(void) {
  struct file *f = createf("bla");
  writef(f, "look no overflows", 10);
}

void user_bad5(void) {
  openf(passwd, WRITE);
}

void user_bad6(void) {
  struct file *f = createf("bla");
  writef(f, "hello world", 12);
  closef(f);
  openf(f, READ);
  seekf(f, 6);
  char buf[12];
  readf(f, buf, 6);
  printf("read: %s\n", buf);
}

volatile int nondet;

void user_main(void) {
  user_ok();
  if (nondet) user_bad1();
  if (nondet) user_bad2();
  if (nondet) user_bad3();
  if (nondet) user_bad4();
  if (nondet) user_bad5();
  if (nondet) user_bad6();
}
