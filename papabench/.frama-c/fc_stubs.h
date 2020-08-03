/*@
  requires valid_exp: \valid(exp);
  assigns \result, *exp \from x;
 */
float frexpf(float x, int *exp);

/*@
  assigns \result \from x, exp;
 */
double ldexp(double x, int exp);
