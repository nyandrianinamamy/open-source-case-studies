int random() {
  extern int n;
  return n;
}

int main() {
  int r = random();
  return r;
}
