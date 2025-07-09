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

/*
  ROOT has rights over USER:
  - ROOT can read/write files owned by USER;
  - USER cannot read/write files owned by ROOT.
 */
enum user {
  ROOT = 0,
  USER = 1
};


struct file;

void user_main(void);

/*@
  ghost enum user g_cur_user;
*/

enum user get_cur_user(void);

/*
  Opens 'f' for reading or writing.
  Notes:
  - 'f' must be a valid file descriptor;
  - the mode must be valid (READ or WRITE);
  - owner rights must be checked.
  - returns 0 in case of success, 1 otherwise.
*/
/*@
  requires \valid(f);
  requires m == READ || m == WRITE;
  //requires f->owner >= g_cur_user; // cannot be done here, no access to file fields
  assigns *f, \result \from *f, m;
  ensures \result == 0 || \result == 1;
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
