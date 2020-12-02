// Based on MITRE's CWE-190, demonstrative example 2
// https://cwe.mitre.org/data/definitions/190.html

// By default, Frama-C/Eva does not report unsigned overflows as alarms;
// nevertheless, in the code below, Eva reports an alarm when trying to
// write to the (under-allocated) buffer.
// Adding option "-warn-unsigned-overflow" ensures Eva reports the
// overflow as soon as it happens.

#include <stdlib.h>

volatile int _rand;
// returns a random int
int random_int(void) {
  return _rand;
}

int packet_get_int_ok() {
  return random_int() ? 0 : 123456; // ok size
}

int packet_get_int_problem() {
  return random_int() ? 1073741824 : 0; // too large (>= INT_MAX/4)
}

char *packet_get_string(const char *s) {
  return "string";
}

int main() {
  char **response;
  int nresp = packet_get_int_ok();
  if (nresp > 0) {
    response = malloc(nresp*sizeof(char*));
    if (!response) exit(1);
    for (int i = 0; i < nresp; i++) response[i] = packet_get_string(NULL);
    free(response);
  }

  nresp = packet_get_int_problem();
  if (nresp > 0) {
    response = malloc(nresp*sizeof(char*));
    if (!response) exit(1);
    for (int i = 0; i < nresp; i++) response[i] = packet_get_string(NULL);
    free(response);
  }
  return 0;
}
