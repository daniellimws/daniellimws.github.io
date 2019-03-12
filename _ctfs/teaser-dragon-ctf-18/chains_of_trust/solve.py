def undo31(l):
    res = [0] * 32
    for i in range(32):
        c = l[i % 4][i // 4]
        if i % 4 == 1:
            c = c - (i // 4) - 20384
        if i % 4 == 2:
            c = c ^ 0x73AB
        if i % 4 == 3:
            c = c - 9981
        if i % 4 == 0:
            c = c // 123

        res[i] = c % 65536

    return res

def undo4a(s):
    res = [ [0] * 8 for _ in range(4) ]
    for i in range(32):
        res[i // 8][i % 8] = s[i] ^ 0x6666

    return res

def generate_array(n):
    consts = [0x9DF9, 0x65E, 0x3B94, 0xFAD9, 0xC3D9, 0xFE12, 0xA57B, 0x9089, 0x3FAF, 0xBB31, 0x4CAD, 0x1415, 0x74CD, 0xCF0A, 0x1CE1, 0xB55A, 0x54C6, 0x827F, 0x179D, 0x66D9, 0xFF80, 0x8126, 0x5579, 0x4AED, 0x5F7D, 0x430F, 0x2EE4, 0x129C, 0xDBCD, 0xEB50, 0x8DA8, 0xBDD1]
    res = [0] * 32

    for i in range(32):
        m = ((n >> 1) | (n << 15)) % 65536
        n = m ^ consts[i]
        res[i] = n % 256

    return res

def brute_force(buf):
    for i in range(65536):
        if buf == generate_array(i):
            return i

    print("[X] Can't find")

def get_buffers():
    start_addresses = [0x8A0, 0x8C8, 0x8F0, 0x918, 0x940, 0x940, 0x940, 0x968, 0x990, 0x9B8, 0x9E0, 0xA08, 0xA08, 0xA30,  0xA58, 0xA80, 0xAA8, 0xAD0, 0xAF8, 0xB20, 0xB48, 0xB70, 0xB98, 0xB98, 0xBC0, 0xBE8, 0xC10, 0xC38,0xC60, 0xC10, 0xC88, 0xC88]

    mem = open("validation", "rb").read()
    res = []

    for i in range(32):
        start = start_addresses[i]
        res.append(list(mem[start: start+32]))

    return res

buffers = get_buffers()

"""
nums = []
for i in range(32):
    print("[+] Trying {}".format(i))
    nums.append(brute_force(buffers[i]))
"""

nums = [18122, 16775, 21890, 24145, 22241, 22241, 22241, 26214, 13940, 13946, 13928, 13936, 13936, 13934, 13893, 10689, 5546, 5515, 5529, 5561, 5556, 5560, 5581, 5581, 16653, 16660, 16649, 16693, 16694, 16649, 16539, 16539]

nums = undo4a(nums)
flag = undo31(nums)
flag = ''.join(map(chr, flag))
print(flag)
