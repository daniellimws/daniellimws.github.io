import zlib

idat = open("corrupt.png", "rb").read()[0x5f+4:0x5f+722+4]
open("idat", "wb").write(idat)
deflated = zlib.decompress(idat)
open("deflated", "wb").write(deflated)
print(len(deflated))