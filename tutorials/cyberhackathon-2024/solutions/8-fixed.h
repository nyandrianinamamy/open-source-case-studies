#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum mode {
  READ,
  WRITE,
};

enum state {
  CLOSED,
  OPEN_READ,
  OPEN_WRITE,
};

enum user {
  ROOT = 0,
  USER = 1
};


struct file;

void user_main(void);

/*
  Opens file for reading or writing.
  Notes:
  - cannot open files from user ROOT.
*/
int openf(struct file *f, enum mode m);

void closef(struct file *f);

/*
  Writes len bytes from buf into file f.
  Notes:
  - cannot write to files not in OPEN_WRITE state.
*/
int writef(struct file *f, const char *buf, size_t len);

/*
  Writes len bytes from buf into file f.
  Notes:
  - cannot read from files not in OPEN_READ state.
*/
void readf(struct file *f, char *buf, size_t len);

/*
  Sets the offset of file f.
 */
void seekf(struct file *f, unsigned long offset);

/*
  Creates a new file, in CLOSED state.
 */
struct file *createf(const char *name);

extern struct file *passwd;
