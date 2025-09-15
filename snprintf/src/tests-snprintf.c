// Copyright (C) 2019 Miroslaw Toton, mirtoto@gmail.com

// Modified for OSCS testing with Frama-C
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "snprintf.h"
#include "__fc_builtin.h"

#ifndef CUR_TEST
#error CUR_TEST must be defined!
#endif

static char msg[32] = {0, };

#define mu_check(exp) if (exp) return __LINE__;

#define mu_assert_int_eq(exp1, exp2) if ((exp1) != (exp2)) return __LINE__;

#define TEST(ret_expected, msg_expected, ret) { \
    if ((ret_expected) != (ret)) {              \
      return 1;                                 \
    }                                           \
    if ((ret) >= 0) {                           \
      if (msg[(ret)] != '\0') {                 \
        return 2;                               \
      }                                         \
      if (strcmp((msg_expected), msg) != 0) {   \
        return 3;                               \
      }                                         \
    }                                           \
    return 0;                                   \
  }

#define MU_TEST(test) static int test()

MU_TEST(test_buffer_null) {
  int ret = 0;
  for (char *pmsg = NULL;;) {
    ret = my_snprintf(pmsg, (size_t)ret,
                   "%s %s%c : %d", "Hello", "World", '!', 2020);
    mu_check(ret == 19);
    if (pmsg != NULL) {
      strncpy(msg, pmsg, sizeof(msg));
      free(pmsg);
      break;
    } else if (ret > 0) {
      // allocate buffer for output string (+1 because of '\0')
      pmsg = malloc((size_t)++ret);
    }
  }
  TEST(19, "Hello World! : 2020", ret);
}

MU_TEST(test_buffer_length_0) {
  int ret = my_snprintf(msg, 0, "%d", 123);
  TEST(-1, NULL, ret);
}

MU_TEST(test_buffer_length_1) {
  int ret = my_snprintf(msg, 1, "%d", 123);
  TEST(0, "",	ret);
}

MU_TEST(test_buffer_length_2) {
  int ret = my_snprintf(msg, 2, "%d", 123);
  TEST(1, "1", ret);
}

MU_TEST(test_buffer_length_3) {
  int ret = my_snprintf(msg, 3, "%d", 123);
  TEST(2, "12", ret);
}

MU_TEST(test_char_dec) {
  int ret = my_snprintf(msg, sizeof(msg), "%hhd %hhd% hhd %hhu",
                     (char)0, (char)123, (char)123, (char)123);
  TEST(13, "0 123 123 123", ret);
}

MU_TEST(test_char_dec_min_and_max) {
  my_snprintf(msg, sizeof(msg), "%hhd", (char)CHAR_MIN);
  mu_check(atoll(msg) == CHAR_MIN);
  my_snprintf(msg, sizeof(msg), "%hhd", (char)CHAR_MAX);
  mu_check(atoll(msg) == CHAR_MAX);
  return 0;
}

MU_TEST(test_char_dec_negative) {
  int ret = my_snprintf(msg, sizeof(msg), "%hhd% hhd %hhu",
                     (char)-123, (char)-123, (char)-123);
  TEST(12, "-123-123 133", ret);
}

MU_TEST(test_short_dec) {
  int ret = my_snprintf(msg, sizeof(msg), "%hd %hd% hd %hu",
                     (short)0, (short)1230, (short)1230, (short)1230);
  TEST(16, "0 1230 1230 1230", ret);
}

MU_TEST(test_short_dec_min_and_max) {
  my_snprintf(msg, sizeof(msg), "%hd", (short)SHRT_MIN);
  mu_check(atoll(msg) == SHRT_MIN);
  my_snprintf(msg, sizeof(msg), "%hd", (short)SHRT_MAX);
  mu_check(atoll(msg) == SHRT_MAX);
  return 0;
}

MU_TEST(test_short_dec_negative) {
  int ret = my_snprintf(msg, sizeof(msg), "%hd% hd %hu",
                     (short)-1230, (short)-1230, (short)-1230);
  TEST(16, "-1230-1230 64306", ret);
}

MU_TEST(test_int_dec) {
  int ret = my_snprintf(msg, sizeof(msg), "%d %d% d %u", 0, 123, 123, 123);
  TEST(13, "0 123 123 123", ret);
}

MU_TEST(test_int_dec_min_and_max) {
  my_snprintf(msg, sizeof(msg), "%d", INT_MIN);
  mu_check(atoll(msg) == INT_MIN);
  my_snprintf(msg, sizeof(msg), "%d", INT_MAX);
  mu_check(atoll(msg) == INT_MAX);
  return 0;
}

MU_TEST(test_int_dec_negative) {
  int ret = my_snprintf(msg, sizeof(msg), "%d% d %u", -123, -123, -123);
  TEST(19, "-123-123 4294967173", ret);
}

MU_TEST(test_int_dec_width_10) {
  int ret = my_snprintf(msg, sizeof(msg), "%10d", -123);
  TEST(10, "      -123", ret);
}

MU_TEST(test_int_dec_width_31_and_0_padded) {
  int ret = my_snprintf(msg, sizeof(msg), "%031d", 123);
  TEST(31, "0000000000000000000000000000123", ret);
}

MU_TEST(test_int_dec_width_31_and_align_left) {
  int ret = my_snprintf(msg, sizeof(msg), "%-31d", 123);
  TEST(31, "123                            ", ret);
}

MU_TEST(test_int_dec_width_2) {
  int ret = my_snprintf(msg, sizeof(msg), "%2d", 123);
  TEST(3, "123", ret);
}

MU_TEST(test_int_dec_width_20_precision_10) {
  int ret = my_snprintf(msg, sizeof(msg), "%20.10d", 123);
  TEST(20, "          0000000123", ret);
}

MU_TEST(test_int_dec_precision_0) {
  int ret = my_snprintf(msg, sizeof(msg), "%.0d %.0d", 123, 0);
  TEST(4, "123 ", ret);
}

MU_TEST(test_int_dec_width_as_parameter) {
  int ret = my_snprintf(msg, sizeof(msg), "%*d", 5, 123);
  TEST(5, "  123", ret);
}

MU_TEST(test_int_dec_random) {
  int d = Frama_C_interval(0, INT_MAX);
  my_snprintf(msg, sizeof(msg), "%d", d);
  mu_check(atoll(msg) == d);
  return 0;
}

MU_TEST(test_int_hex) {
  int ret = my_snprintf(msg, sizeof(msg), "%x %x %#x", 0, 123, 123);
  TEST(9, "0 7b 0x7b", ret);
}

MU_TEST(test_int_hex_uppercase) {
  int ret = my_snprintf(msg, sizeof(msg), "%X %#X", 123, 123);
  TEST(7, "7B 0X7B", ret);
}

MU_TEST(test_int_hex_negative) {
  const char expected[] = "ffffffffffffff85";
  int x = -123;
  int ret = my_snprintf(msg, sizeof(msg), "%x", x);
  TEST(sizeof(x) * 2, expected + strlen(expected) - sizeof(x) * 2, ret);
}

MU_TEST(test_int_hex_precision_0) {
  int ret = my_snprintf(msg, sizeof(msg), "%#.0x %#.0x", 123, 0);
  TEST(5, "0x7b ", ret);
}

MU_TEST(test_long_dec) {
  int ret = my_snprintf(msg, sizeof(msg), "%ld", 123000l);
  TEST(6, "123000", ret);
}

MU_TEST(test_long_hex) {
  int ret = my_snprintf(msg, sizeof(msg), "%lx %lX", 123000l, 123000l);
  TEST(11, "1e078 1E078", ret);
}

MU_TEST(test_long_hex_alternative) {
  int ret = my_snprintf(msg, sizeof(msg), "%#lx %#lX", 123000l, 123000l);
  TEST(15, "0x1e078 0X1E078", ret);
}

MU_TEST(test_long_hex_width_as_type) {
  const char expected[] = "0000000000000000000000000001e078";
  long x = 123000l;
  int ret = my_snprintf(msg, sizeof(msg), "%0*lx", (int)(sizeof(x) * 2), x);
  TEST(sizeof(x) * 2, expected + strlen(expected) - sizeof(x) * 2, ret);
}

MU_TEST(test_long_long_dec) {
  int ret = my_snprintf(msg, sizeof(msg), "%lld", 123000000000ll);
  TEST(12, "123000000000", ret);
}

MU_TEST(test_long_long_dec_min) {
  long long d = LLONG_MIN;
  my_snprintf(msg, sizeof(msg), "%lld", d);
  mu_check(atoll(msg) == d);
  return 0;
}

MU_TEST(test_long_long_dec_max) {
  long long d = LLONG_MAX;
  my_snprintf(msg, sizeof(msg), "%lld", d);
  mu_check(atoll(msg) == d);
  return 0;
}

MU_TEST(test_long_long_hex) {
  int ret = my_snprintf(msg, sizeof(msg), "%llx %llX", 123000000000ll, 123000000000ll);
  TEST(21, "1ca35f0e00 1CA35F0E00", ret);
}

MU_TEST(test_long_long_hex_alternative) {
  int ret = my_snprintf(msg, sizeof(msg), "%#llx %#llX", 123000000000ll, 123000000000ll);
  TEST(25, "0x1ca35f0e00 0X1CA35F0E00", ret);
}

MU_TEST(test_long_long_hex_width_as_type) {
  const char expected[] = "00000000000000000000001ca35f0e00";
  long long x = 123000000000ll;
  int ret = my_snprintf(msg, sizeof(msg), "%0*llx", (int)(sizeof(x) * 2), x);
  TEST(sizeof(x) * 2, expected + strlen(expected) - sizeof(x) * 2, ret);
}

MU_TEST(test_long_long_hex_max) {
  char expected[] = "ffffffffffffffffffffffffffffffff";
  unsigned long long x = ULLONG_MAX;
  int ret = my_snprintf(msg, sizeof(msg), "%llx", x);
  expected[sizeof(x) * 2] = '\0';
  TEST(sizeof(x) * 2, expected, ret);
}

MU_TEST(test_double_f) {
  int ret = my_snprintf(msg, sizeof(msg), "%f %f %F",
                     0.0, 123.0, 123.0 + 1.0 / 3);
  TEST(30, "0.000000 123.000000 123.333333", ret);
}

MU_TEST(test_double_f_precision_0) {
  int ret = my_snprintf(msg, sizeof(msg), "%.0f %.0f %.0F",
                     0.0, 123.0, 123.0 + 1.0 / 3);
  TEST(9, "0 123 123", ret);
}

MU_TEST(test_double_f_precision_2_3) {
  int ret = my_snprintf(msg, sizeof(msg), "%2.3f %2.3f %2.3F",
                     0.0, 123.0, 123.0 + 1.0 / 3);
  TEST(21, "0.000 123.000 123.333", ret);
}

MU_TEST(test_double_e_zero) {
  int ret = my_snprintf(msg, sizeof(msg), "%e %E", 0.0, 0.0);
  TEST(25, "0.000000e+00 0.000000E+00", ret);
}

MU_TEST(test_double_e) {
  int ret = my_snprintf(msg, sizeof(msg), "%e %E",
                     123.0 + 1.0 / 3, 123.0 + 1.0 / 3);
  TEST(25, "1.233333e+02 1.233333E+02", ret);
}

MU_TEST(test_double_e_precision_0) {
  int ret = my_snprintf(msg, sizeof(msg), "%.0e %.0E %.0e %.0E",
                     0.0, 0.0, 123.0 + 1.0 / 3, 123.0 + 1.0 / 3);
  TEST(23, "0e+00 0E+00 1e+02 1E+02", ret);
}

MU_TEST(test_double_e_precision_2_3) {
  int ret = my_snprintf(msg, sizeof(msg), "%2.3e %2.3E",
                     123.0 + 1.0 / 3, 123.0 + 1.0 / 3);
  TEST(19, "1.233e+02 1.233E+02", ret);
}

MU_TEST(test_double_g) {
  int ret = my_snprintf(msg, sizeof(msg), "%g %G",
                     123.0 + 1.0 / 3, 123.0 + 1.0 / 3);
  TEST(21, "123.333333 123.333333", ret);
}

MU_TEST(test_double_g_precision_0) {
  int ret = my_snprintf(msg, sizeof(msg), "%.0g %.0G %.0g %.0G",
                     0.0, 0.0, 1.0 / 123000000.0, 1.0 / 123000000.0);
  TEST(23, "0e+00 0E+00 8e-09 8E-09", ret);
}

MU_TEST(test_double_g_precision_2_7) {
  int ret = my_snprintf(msg, sizeof(msg), "%2.7g %2.7G",
                     1.0 / 123000000.0, 1.0 / 123000000.0);
  TEST(27, "8.1300813e-09 8.1300813E-09", ret);
}

MU_TEST(test_string) {
  int ret = my_snprintf(msg, sizeof(msg), "%s", "Hello");
  TEST(5, "Hello", ret);
}

MU_TEST(test_string_empty) {
  int ret = my_snprintf(msg, sizeof(msg), "%s", "");
  TEST(0, "", ret);
}

MU_TEST(test_string_width_20) {
  int ret = my_snprintf(msg, sizeof(msg), "%20s", "Hello");
  TEST(20, "               Hello", ret);
}

MU_TEST(test_string_width_20_and_align_left) {
  int ret = my_snprintf(msg, sizeof(msg), "%-20s", "Hello");
  TEST(20, "Hello               ", ret);
}

MU_TEST(test_string_width_20_precision_2) {
  int ret = my_snprintf(msg, sizeof(msg), "%20.2s", "Hello");
  TEST(20, "                  He", ret);
}

MU_TEST(test_string_width_20_precision_20) {
  int ret = my_snprintf(msg, sizeof(msg), "%20.20s", "Hello");
  TEST(20, "               Hello", ret);
}

MU_TEST(test_string_with_less_than_input) {
  int ret = my_snprintf(msg, sizeof(msg), "%3s", "Hello");
  TEST(5, "Hello", ret);
}

MU_TEST(test_string_with_less_than_input_precision_equal_width) {
  int ret = my_snprintf(msg, sizeof(msg), "%3.3s", "Hello");
  TEST(3, "Hel", ret);
}

MU_TEST(test_string_width_as_parameter) {
  int ret = my_snprintf(msg, sizeof(msg), "%-*.s%*.s!", 10, "Hello", 10, "World");
  TEST(21, "Hello          World!", ret);
}

MU_TEST(test_string_precision_as_parameter) {
  int ret = my_snprintf(msg, sizeof(msg), "%-.*s%.*s!", 10, "Hello", 10, "World");
  TEST(11, "HelloWorld!", ret);
}

MU_TEST(test_string_width_and_precision_as_parameter) {
  int ret = my_snprintf(msg, sizeof(msg), "%-*.*s%*.*s!",
                     10, 10, "Hello", 10, 10, "World");
  TEST(21, "Hello          World!", ret);
}

MU_TEST(test_string_width_as_parameter_negative) {
  int ret = my_snprintf(msg, sizeof(msg), "%*s", -20, "Hello World!");
  TEST(12, "Hello World!", ret);
}

MU_TEST(test_string_too_long) {
  const char *str = "This is very long message and it is much longer than buffer!";
  int ret = my_snprintf(msg, sizeof(msg), "%s", str);
  TEST(sizeof(msg) - 1, "This is very long message and i", ret);
}

MU_TEST(test_strings) {
  int ret = my_snprintf(msg, sizeof(msg), "%s %s%c", "Hello", "World", '!');
  TEST(12, "Hello World!", ret);
}

MU_TEST(test_chars) {
  int ret = my_snprintf(msg, sizeof(msg), "%c%c%c%c%c", 'H', 'e', 'l', 'l', 'o');
  TEST(5, "Hello", ret);
}

MU_TEST(test_pointer_null) {
  int ret = my_snprintf(msg, sizeof(msg), "%p", (void *)0);
  TEST(5, "(nil)", ret);
}

MU_TEST(test_pointer) {
  int ret = my_snprintf(msg, sizeof(msg), "%p", (void *)0x12345678aabbccdd);
  TEST(18, "0x12345678aabbccdd", ret);
}

MU_TEST(test_percent) {
  const char *str = "%%%%% Hello World! %%%%%";
  int ret = my_snprintf(msg, sizeof(msg), "%%%%%%%%%% Hello World! %%%%%%%%%%");
  TEST((int)strlen(str), str, ret);
}

MU_TEST(test_counters) {
  int counter1 = 0, counter2 = 0;
  int ret = my_snprintf(msg, sizeof(msg), "%s%n %s%n%c",
                     "Hello", &counter1, "World", &counter2, '!');
  mu_assert_int_eq(5, counter1);
  mu_assert_int_eq(11, counter2);
  TEST(12, "Hello World!", ret);
}

int test_number = 0;

#define RUN_TEST(test) {                        \
    test_number++;                              \
    if (test_number == CUR_TEST) {              \
      int r = test();                           \
      if (r) {                                  \
        return r;                               \
      }                                         \
    }                                           \
  }

int run() {
  int test_number = 0;

  RUN_TEST(test_buffer_null);
  RUN_TEST(test_buffer_length_0);
  RUN_TEST(test_buffer_length_1);
  RUN_TEST(test_buffer_length_2);
  RUN_TEST(test_buffer_length_3);

  RUN_TEST(test_char_dec);
  RUN_TEST(test_char_dec_min_and_max);
  RUN_TEST(test_char_dec_negative);

  RUN_TEST(test_short_dec);
  RUN_TEST(test_short_dec_min_and_max);
  RUN_TEST(test_short_dec_negative);

  RUN_TEST(test_int_dec);
  RUN_TEST(test_int_dec_min_and_max);
  RUN_TEST(test_int_dec_negative);
  RUN_TEST(test_int_dec_width_10);
  RUN_TEST(test_int_dec_width_31_and_0_padded);
  RUN_TEST(test_int_dec_width_31_and_align_left);
  RUN_TEST(test_int_dec_width_2);
  RUN_TEST(test_int_dec_width_20_precision_10);
  RUN_TEST(test_int_dec_precision_0);
  RUN_TEST(test_int_dec_width_as_parameter);
  RUN_TEST(test_int_dec_random);

  RUN_TEST(test_int_hex);
  RUN_TEST(test_int_hex_uppercase);
  RUN_TEST(test_int_hex_negative);
  RUN_TEST(test_int_hex_precision_0);

  RUN_TEST(test_long_dec);
  RUN_TEST(test_long_hex);
  RUN_TEST(test_long_hex_alternative);
  RUN_TEST(test_long_hex_width_as_type);

  RUN_TEST(test_long_long_dec);
  RUN_TEST(test_long_long_dec_min);
  RUN_TEST(test_long_long_dec_max);
  RUN_TEST(test_long_long_hex);
  RUN_TEST(test_long_long_hex_alternative);
  RUN_TEST(test_long_long_hex_width_as_type);
  RUN_TEST(test_long_long_hex_max);

  RUN_TEST(test_double_f);
  RUN_TEST(test_double_f_precision_0);
  RUN_TEST(test_double_f_precision_2_3);
  RUN_TEST(test_double_e);
  RUN_TEST(test_double_e_zero);
  RUN_TEST(test_double_e_precision_0);
  RUN_TEST(test_double_e_precision_2_3);
  RUN_TEST(test_double_g);
  RUN_TEST(test_double_g_precision_0);
  RUN_TEST(test_double_g_precision_2_7);

  RUN_TEST(test_string);
  RUN_TEST(test_string_empty);
  RUN_TEST(test_string_width_20);
  RUN_TEST(test_string_width_20_and_align_left);
  RUN_TEST(test_string_width_20_precision_2);
  RUN_TEST(test_string_width_20_precision_20);
  RUN_TEST(test_string_with_less_than_input);
  RUN_TEST(test_string_with_less_than_input_precision_equal_width);
  RUN_TEST(test_string_width_as_parameter);
  RUN_TEST(test_string_precision_as_parameter);
  RUN_TEST(test_string_width_and_precision_as_parameter);
  RUN_TEST(test_string_width_as_parameter_negative);
  RUN_TEST(test_string_too_long);

  RUN_TEST(test_strings);
  RUN_TEST(test_chars);

  RUN_TEST(test_pointer_null);
  RUN_TEST(test_pointer);

  RUN_TEST(test_percent);
  RUN_TEST(test_counters);

  return 0;
}

int main(void) {
  return run();
}
