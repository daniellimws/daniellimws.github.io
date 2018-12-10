#!/usr/bin/python

from __future__ import print_function
from unicorn import *
from unicorn.x86_const import *
from pwn import *

def getxmm0(n):
    # code to be emulated
    X86_CODE32 = asm("cvtdq2pd xmm0, xmm0")
    X86_CODE32 += asm("mulsd xmm0, xmm1")

    # memory address where emulation starts
    ADDRESS = 0x1000000

    try:
        mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(ADDRESS, 2 * 1024 * 1024)
        mu.mem_write(ADDRESS, X86_CODE32)
        mu.reg_write(UC_X86_REG_XMM0, n)
        mu.reg_write(UC_X86_REG_XMM1, 0x00000000000000004036800000000000)
        mu.emu_start(ADDRESS, ADDRESS + len(X86_CODE32))

        r_xmm0 = mu.reg_read(UC_X86_REG_XMM0)
        return r_xmm0

    except UcError as e:
        print("ERROR: %s" % e)

if __name__ == "__main__":
    flag = ''

    d = {}
    for i in range(0x10):
        d[getxmm0(i)] = i

    dump = open("dump.bin").read()
    assert len(dump) == 16 * 24

    for i in range(0, len(dump), 16):
        x = dump[i:i+8]
        x = u64(x)
        y = dump[i+8:i+16]
        y = u64(y)

        z = d[x] * 0x10 + d[y]
        flag += chr(z)

    print(flag)


