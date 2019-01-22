from pwn import *

p = remote("206.189.93.101", 4343)

p.sendline("start")

for i in range(30):
    p.recvuntil("/30] ")
    exp = p.recv(7).replace("x", "*")
    ans = str(eval(exp))
    p.sendline(ans)
    print exp + " = " + ans

p.interactive()