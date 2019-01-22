from pwn import *
import string

p = remote("178.128.62.127", 5000)

flag = ""
padding = "A" * 15
block_size = 16

def get_enc(p):
    p.recvuntil("(in hex): ")
    return p.recvline().strip()

while True:
    block_num = len(flag) // block_size
    use_padding = padding[:len(padding) - (len(flag) % block_size)]
    if len(use_padding) == 0:
        p.sendline("A" * 16)
        correct = get_enc(p)[block_size * (block_num + 1) * 2:block_size * 2 * (block_num + 2)]
    else:
        p.sendline(use_padding)
        correct = get_enc(p)[block_size * block_num * 2:block_size * 2 * (block_num + 1)]
    for guess in string.printable:
        p.sendline(use_padding + flag + guess)
        c = get_enc(p)[block_size * block_num * 2:block_size * 2 * (block_num + 1)]
        if c == correct:
            flag += guess
            print flag
            break

