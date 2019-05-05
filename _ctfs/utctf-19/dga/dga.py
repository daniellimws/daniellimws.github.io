# uncompyle6 version 2.11.5
# Python bytecode 3.6 (3379)
# Decompiled from: Python 2.7.10 (default, Feb 22 2019, 21:17:52) 
# [GCC 4.2.1 Compatible Apple LLVM 10.0.1 (clang-1001.0.37.14)]
# Embedded file name: dga.py
from nistbeacon import NistBeacon
import time
import hashlib

def gen_domain():
    now = int(time.time())
    now -= 100000000
    record = NistBeacon.get_previous(now)
    val = record.output_value
    h = hashlib.md5()
    h.update(str(val).encode('utf-8'))
    res = h.digest()
    domain = ''
    for ch in res:
        tmp = (ch & 15) + (ch >> 4) + ord('a')
        if tmp <= ord('z'):
            domain += chr(tmp)

    domain += '.org'


if __name__ == '__main__':
    gen_domain()