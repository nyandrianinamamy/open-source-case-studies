#include "8.h"

#define BUF_SIZE 64
#define FILENAME_SIZE 16

struct file {
  char name[FILENAME_SIZE];
  int owner;
  enum state state;
  unsigned long offset;
  char buf[BUF_SIZE]; // emulates the actual file contents
};

static enum user cur_user;

enum user get_cur_user() {
  return cur_user;
}

/*@
  requires f->owner >= g_cur_user;
 */
int openf(struct file *f, enum mode m);int openf(struct file *f, enum mode m) {
  if (f->owner == ROOT) {
    // access denied
    return 1;
  }
  f->offset = 0;
  return 0;
}

void closef(struct file *f) {
  f->state = CLOSED;
}

int writef(struct file *f, const char *buf, size_t len) {
  if (f->owner == ROOT) {
    return 1;
  }
  memcpy(f->buf, buf, len);
  return 0;
}

void readf(struct file *f, char *buf, size_t len) {
  memcpy(buf, f->buf + f->offset, len);
}

void seekf(struct file *f, unsigned long offset) {
  f->offset = offset;
}

struct file *createf(const char *name) {
  struct file *f = malloc(sizeof(struct file));
  if (!f) return NULL;
  strcpy(f->name, name);
  f->owner = USER;
  f->state = CLOSED;
  f->offset = 0;
  return f;
}

struct file fpasswd = {
  .name = "passwd",
  .owner = ROOT,
  .state = CLOSED,
  .offset = 0,
};

struct file *passwd = &fpasswd;

int main() {
  // init root files
  cur_user = ROOT;
  //@ ghost g_cur_user = ROOT;
  strcpy(fpasswd.buf, "root\n");
  cur_user = USER;
  //@ ghost g_cur_user = USER;
  user_main();
  return 0;
}
