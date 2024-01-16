extern unsigned char p[19][19], ma[19][19], ml[19][19];
extern int mik, mjk;
extern int mymove;
extern int lib;
extern int play, pass;

/*@
  assigns \result, *i, *j, *val \from indirect:m,
                                      indirect:n,
                                      indirect:p[0..18][0..18],
                                      indirect:ma[0..18][0..18];
*/
int findnextmove(int m, int n, int *i, int *j, int *val, int minlib);

/*@
  assigns ml[0..18][0..18] \from indirect:i,
                                 indirect:j,
                                 indirect:color,
                                 indirect:p[0..18][0..18],
                                 indirect:ml[0..18][0..18];
  assigns lib \from lib,
                    indirect:i,
                    indirect:j,
                    indirect:color,
                    indirect:p[0..18][0..18],
                    indirect:ml[0..18][0..18];
*/
void count(int i, int j, int color);

/*@
  assigns play, pass, *i, *j \from indirect:move[..]; //missing: \from filesystem
                                                  //(gnugo.dat);
*/
void getmove(char move[], int *i, int *j);

/*@
  assigns ma[0..18][0..18] \from indirect:m,
                                 indirect:n,
                                 indirect:i[..],
                                 indirect:j[..],
                                 indirect:color,
                                 indirect:minlib,
                                 indirect:*ct,
                                 indirect:p[0..18][0..18],
                                 indirect:ma[0..18][0..18],
                                 indirect:mik,
                                 indirect:mjk;
  assigns *ct \from *ct,
                    indirect:m,
                    indirect:n,
                    indirect:i[..],
                    indirect:j[..],
                    indirect:color,
                    indirect:minlib,
                    indirect:p[0..18][0..18],
                    indirect:ma[0..18][0..18],
                    indirect:mik,
                    indirect:mjk;
  assigns i[..] \from direct:m,
                      indirect:n,
                      indirect:i[..],
                      indirect:j[..],
                      indirect:color,
                      indirect:minlib,
                      indirect:*ct,
                      indirect:p[0..18][0..18],
                      indirect:ma[0..18][0..18],
                      indirect:mik,
                      indirect:mjk;
  assigns j[..] \from indirect:m,
                      indirect:n,
                      indirect:i[..],
                      indirect:j[..],
                      indirect:color,
                      indirect:minlib,
                      indirect:*ct,
                      indirect:p[0..18][0..18],
                      indirect:ma[0..18][0..18],
                      indirect:mik,
                      indirect:mjk;
  assigns \result \from indirect:m,
                        indirect:n,
                        indirect:i[..],
                        indirect:j[..],
                        indirect:color,
                        indirect:minlib,
                        indirect:*ct,
                        indirect:p[0..18][0..18],
                        indirect:ma[0..18][0..18],
                        indirect:mik,
                        indirect:mjk;
*/
int findopen(int m, int n, int i[], int j[], int color, int minlib, int *ct);
