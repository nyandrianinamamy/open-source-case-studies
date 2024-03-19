
extern unsigned char p[19][19], ma[19][19], ml[19][19], l[19][19];
extern int mik, mjk;
extern int mymove,umove;
extern int lib;
extern int play, pass;

// #define _FC_ACTIVE_LONG_PROOF
//@ predicate in_grid(integer x) = 0 <= x < 19;

/*@
  requires in_grid_i: in_grid(i);
  requires in_grid_j: in_grid(j);
*/
void countlib(int i, int j, int color);

/*@
  requires in_grid_i: in_grid(i);
  requires in_grid_j: in_grid(j);
*/
int fioe(int i,   /* stone row number 0 to 18 */
         int j);   /* stone column number 0 to 18 */

/* @
  requires \initialized(move + 1);
  ensures in_grid_i: \result==1 ==> in_grid(*i);
  ensures in_grid_j: \result==1 ==> in_grid(*j);
*/
int getij(char move[],   /* move string */
          int *i,        /* move row number */
          int *j);        /* move column number */

/*@
  ensures in_grid_i: !pass ==> in_grid(*i);
  ensures in_grid_j: !pass ==> in_grid(*j);
*/
void genmove(int *i, int *j);

/*@
  assigns \result, *i, *j, *val \from
                    indirect:*val,
                    indirect:p[0..18][0..18],
                    indirect:lib,
                    indirect:l[0..18][0..18],
                    indirect:umove;
  assigns lib \from indirect:l[0..18][0..18],
                    indirect:p[0..18][0..18],
                    indirect:umove,
                    indirect:lib;
  assigns p[0..18][0..18] \from
                  mymove,
                  indirect:l[0..18][0..18],
                  indirect:p[0..18][0..18],
                  indirect:umove,
                  indirect:lib;
  ensures \result==1 ==> 0<=*i<19;
  ensures \result==1 ==> 0<=*j<19;
*/
int findwinner(int *i,    /* row number of next move */
               int *j,    /* column number of next move */
               int *val);  /* value of next move */

/*************************************************
 * Recursive functions
**************************************************/
/* count, findwinr, findnext, getmove, findopen */

/*@
  requires in_grid_i: in_grid(i);
  requires in_grid_j: in_grid(j);
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
  ensures 0 <= lib <= 360;
*/
void count(int i, int j, int color);

/*@
  assigns \result, *i, *j, *val \from indirect:m,
                                      indirect:n,
                                      indirect:p[0..18][0..18],
                                      indirect:ma[0..18][0..18];
*/
int findnextmove(int m, int n, int *i, int *j, int *val, int minlib);

/*@
  requires \valid(i);
  requires \valid(j);
  requires \valid(move);
  assigns play, pass, *i, *j \from indirect:move[..]; //missing: \from filesystem
                                                  //(gnugo.dat);
  ensures play:in_grid_i: (play && !pass) ==> in_grid(*i);
  ensures play:in_grid_j: (play && !pass) ==> in_grid(*j);
  ensures endOrPass: *i==\at(*i, Old);
  ensures endOrPass: *j==\at(*j, Old);
  ensures Pass: *i == -1;
*/
void getmove(char move[], int *i, int *j);

/*@
  assigns ma[0..18][0..18] \from indirect:m,
                                 indirect:n,
                                 indirect:color,
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
                    indirect:p[0..18][0..18],
                    indirect:ma[0..18][0..18],
                    indirect:mik,
                    indirect:mjk;
  assigns i[..] \from m,
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
  assigns j[..] \from n,
                      indirect:m,
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
