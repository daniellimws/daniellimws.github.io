from binascii import unhexlify, hexlify
from pwn import xor
from string import printable

c1 = b"b99e9a7ebbd764933aa2bf98f2f0485aa0d38c73f5ce29d823e7f285bbb0524bbdc5cd34b89c41d4"
c1 = unhexlify(c1)

c = b"\xb9"
for i in range(1, len(c1)):
    c += bytes([c1[i-1] ^ c1[i]])
# print(c)

# for i in range(256):
#     key = b'\xce@i\x9d\xbe\x59\xd7\x95' + b'aa' + bytes([i]) + b'\x12\\5\x80t'
#     # print(len(key))

#     d = xor(key, c)

#     # valid = printable.encode()
#     valid = b"0123456789abcdef"
#     # if d[5] in valid and d[21] in valid and d[37] == ord('}'):
#     #     print(i, d)
#     # if d[6] in valid and d[22] in valid:
#     #     print(hex(i), d)
#     if d[10] in valid and d[26] in valid:
#         print(hex(i), d)

# gef➤  grep 0x95d759be little 0x005566aaf07000-0x005566aaf28000
# [+] Searching '\xbe\x59\xd7\x95' in 0x005566aaf07000-0x005566aaf28000
# [+] In 'load6'(0x5566aaf07000-0x5566aaf28000), permission=---
#   0x5566aaf07484 - 0x5566aaf07494  →   "\xbe\x59\xd7\x95[...]" 

# gef➤  x/16bx 0x5566aaf07484-4
# 0x5566aaf07480:	0xce	0x40	0x69	0x9d	0xbe	0x59	0xd7	0x95
# 0x5566aaf07488:	0x98	0xa1	0x2d	0x14	0x0f	0x33	0x81	0x20

key = unhexlify(b"ce40699dbe59d79598a12d140f338120")
print(xor(key, c))