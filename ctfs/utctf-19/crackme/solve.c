#include <stdio.h>

int main() {
    char flag[0x41];
    fgets(flag, 0x40, stdin);

    for (int i = 0; i < 0x40; ++i) {
        flag[i] = flag[i] ^ (0x33 + i);
        flag[i] ^= 0x27;
    }

    flag[47] = '_';
    flag[52] = '0';
    flag[0x39] = '\x00';

    puts(flag);
}