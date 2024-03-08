
#include <inttypes.h>
#include <stdio.h>
#include "__fc_builtin.h"

#include "../src/permutations.h"


int main() {
    permutations_t p = perm_init(10, "0123456789");

    // printf("%s\n", perm_to_string(p));
    for (uint64_t i = 0; i < Frama_C_size_t_interval(1,100000000); ++i) {
        perm_add(p, Frama_C_size_t_interval(1,100000000));
        // printf("%s\n", perm_to_string(p));
    }

    // printf("----------------------------------------------------------------\n");

    // for (uint64_t i = 0; i < 23; ++i) {
    //     perm_sub(p, 3);
    //     // printf("%s\n", perm_to_string(p));
    // }

    perm_free(p);
}
