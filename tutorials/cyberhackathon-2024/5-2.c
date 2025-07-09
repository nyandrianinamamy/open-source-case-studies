#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 8

struct student {
  char name[N];
  float grade;
};

int main() {
  char buf[N];
  printf("Enter the student's name:\n");
  char *r = fgets(buf, N, stdin);
  if (!r) {
    printf("Error reading name\n");
    exit(1);
  }
  size_t n = strlen(buf);
  if (n <= 1) {
    printf("Error: invalid name\n");
    exit(1);
  }
  buf[n-1] = '\0'; // remove '\n'
  struct student stu;
  strcpy(stu.name, buf);
  printf("Enter the student's grade (between 0 and 20):\n");
  r = fgets(buf, N, stdin);
  if (!r) {
   printf("Error: invalid grade\n");
    exit(1);
  }
  char *endbuf;
  stu.grade = strtof(buf, &endbuf);
  if (buf == endbuf) {
    printf("Error: invalid grade\n");
    exit(1);
  }
  if (stu.grade < 0 || stu.grade > 20) {
    printf("Error: grade out of bounds\n");
    exit(1);
  }
  printf("%s's grade: %2.1f\n", stu.name, stu.grade);

  return 0;
}
