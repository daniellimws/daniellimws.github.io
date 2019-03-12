import hashlib
import string

def read_hashes(f):
    hashes = open(f, "r").read()
    hashes = [hashes[i*32:(i+1)*32].decode("hex") for i in range(70)]
    return hashes

def rot13(s):
    tr = string.maketrans( 
        "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz", 
        "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm")
    return string.translate(s, tr)

def solve(target):
    for c in string.printable:
        b64 = c.encode("base64")[:-1]
        m = hashlib.md5(b64).hexdigest()
        m = hashlib.md5(m).hexdigest()
        m = m.decode("hex")
        if target == m:
            return c
    
    raise Exception("gg cannot find")

hashes = read_hashes("hashes.bin")
flag = ""
for h in hashes:
    flag += rot13(solve(h))

print flag