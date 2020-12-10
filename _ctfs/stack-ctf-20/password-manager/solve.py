from z3 import *

# Combine 4 single bytes to a block of 4 bytes
def pack_bv(a):
    return Concat(a[3], a[2], a[1], a[0])

def pack_arr(arr):
    res = []
    for i in range(8):
        res.append(pack_bv(arr[i*4:i*4+4]))
    return res

# Split a block of 4 bytes into 4 single bytes
def unpack_bv(n):
    res = [0,0,0,0]
    res[3] = Extract(31, 24, n)
    res[2] = Extract(23, 16, n)
    res[1] = Extract(15, 8, n)
    res[0] = Extract(7, 0, n)
    return res

def unpack_arr(arr):
    res = []
    for i in range(8):
        res += unpack_bv(arr[i])
    return res

func_1_offsets = [166, 192, 238, 68, 225, 61, 74, 62, 29, 110, 6, 166, 23, 171, 20, 225, 124, 122, 182, 29, 217, 123, 48, 23, 168, 116, 4, 124, 210, 186, 165, 217]

def func1(arr):
    res = []
    for i in range(32):
        res.append(arr[i])

    for i in range(32):
        res[i] = res[i] + func_1_offsets[i]

    return res

def func2(arr):
    arr = pack_arr(arr)
    res = []
    for i in range(8):
        res.append(arr[i])

    for i in range(7):
        b1_idx = i
        b1 = res[b1_idx]
        d1 = b1

        b2_idx = i + 1
        b2 = res[b2_idx]
        d2 = b2

        res[b2_idx] = RotateRight(d1, 20) ^ d2
        res[b1_idx] = RotateRight(d1, 20)

    res = unpack_arr(res)
    return res

func_4_indices = [0x1d,0xd,0x10,0x14,4,0x16,0x15,0x18,0x1f,0xb,1,0,9,7,8,5,0x19,6,0x13,0xf,0x17,0x1b,3,2,0x1a,0x12,0x1e,0x1c,10,0xc,0x11,0xe]

def func4(arr, start):
    res = []
    for i in range(32):
        res.append(arr[i])

    for _ in range(16):
        i1 = func_4_indices[(start) % 32]
        i2 = func_4_indices[(start + 1) % 32]

        res[i1], res[i2] = res[i2], res[i1]
        tmp = URem(res[i2], 0x46) + res[i1]
        res[i1] = tmp
        res[i2] = res[i2] + URem(tmp, 0x32)

        start += 2
        start %= 32

    return res

password_bvs = []
for i in range(32):
    password_bvs.append(BitVec("password_8_" + str(i), 8))

password = func1(password_bvs)
password = func4(password, 1)
password = func2(password)
password = func1(password)
password = func4(password, 13)
password = func2(password)

solver = Solver()

correct = [0x76, 0xcf, 0x96, 0x48, 0x70, 0x61, 0x04, 0x8c, 0x1f, 0xc5, 0x25, 0xf3, 0xdc, 0xa0, 0x3c, 0xc8, 0x92, 0x8a, 0x2d, 0xeb, 0x24, 0x65, 0x8c, 0xf5, 0xd6, 0xb8, 0x11, 0x04, 0x6d, 0x90, 0x08, 0x60]
for i in range(32):
    solver.add(correct[i] == password[i])

print(solver.check())
model = solver.model()

flag = []
for i in range(32):
    d = model[password_bvs[i]].as_long()
    flag.append(d)

print("".join("{:c}".format(s) for s in flag))