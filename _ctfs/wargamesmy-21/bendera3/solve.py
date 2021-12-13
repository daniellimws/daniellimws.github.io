from pwn import xor
from binascii import unhexlify

aaa = unhexlify("kxk1x4xxkx11O4TxkOc6xxb64Obxk1613xdxx1F11x9OT6Txd31xcOd1O1OOcO64"[::-1].replace("O", "0").replace("T", "7").replace("b", "8").replace("x", "5").replace("F", "f").replace("k", "e"))

print(b"wgmy{" + xor(aaa, "th1s-i5_4_k3y") + b"}")

# wgmy{2d1c0edbc8bbfa5be3117a3ed9e6d637}