---
layout: post
title: Hfs-mbr (re213)
ctf: Midnight Sun CTF Quals 2019
---

> We made a military-grade secure OS for HFS members. Feel free to beta test it for us!
>
> Download: [hfs-os.tar.gz][download]

First thing to do is to extract the files in the archive.

```bash
➤ tar -xf ../hfs-os.tar.gz
➤ ls -l
total 20496
-rw-r--r--@ 1 daniellimws  staff       405 Apr  4 21:39 README
drwxr-xr-x@ 7 daniellimws  staff       224 Mar 28 01:46 bin
-rw-r--r--@ 1 daniellimws  staff  10485760 Apr  4 09:27 dos.img
-rwxr-xr-x@ 1 daniellimws  staff       288 Apr  4 06:09 run
```

```bash
➤ cat README
HFS-OS
./run debug (gdb stub) or ./run

How to debug with IDA
In IDA > Debugger > Attach > Remote debugger (host:1234) > (Debug options > Set specific options, UNCHECK 'software breakpoints at eip+1', CHECK 'use CS:IP in real mode')  > OK
When attached, Debugger > Manual memory regions > Insert > CHECK 16bit segment > OK
In the IDA-View, press G, 0x7c00 is where the bootloader starts. Set a BP > F9
```

We are given a wrapper script for loading the challenge in `QEMU`.

```bash
➤ cat run
#! /bin/bash

if [ "$1" = "debug" ] ; then
    cd bin && ./`QEMU`-system-i386 -s -S -m 16 -k en-us -rtc base=localtime -nographic -drive file=../dos.img -boot order=c
else
    cd bin && ./`QEMU`-system-i386 -m 16 -k en-us -rtc base=localtime -nographic -drive file=../dos.img -boot order=c
fi
```

Nothing much of our interest in *bin/*, just stuff for `QEMU`.

```bash
➤ ls -al bin
total 120824
drwxr-xr-x@ 7 daniellimws  staff       224 Mar 28 01:46 .
drwxr-xr-x  6 daniellimws  staff       192 Apr  8 11:23 ..
-rw-r--r--@ 1 daniellimws  staff    262144 Mar 28 01:45 bios-256k.bin
-rw-r--r--@ 1 daniellimws  staff    240128 Mar 28 01:45 efi-e1000.rom
-rw-r--r--@ 1 daniellimws  staff      9216 Mar 28 01:45 kvmvapic.bin
-rwxr-xr-x@ 1 daniellimws  staff  61304648 Mar 28 01:45 `QEMU`-system-i386
-rw-r--r--@ 1 daniellimws  staff     38912 Mar 28 01:45 vgabios-stdvga.bin
```

*dos.img* here is a MBR boot sector.

```bash
➤ file dos.img
dos.img: DOS/MBR boot sector; partition 1 : ID=0x1, active, start-CHS (0x0,1,1), end-CHS (0x13,15,63), startsector 63, 20097 sectors
```

Executing the `run` script, we will see the following load screen

```
.

[HFS SECURE BOOT] Loading  ...
.-. .-.----.----.   .-.   .-.----..----.
| {_} | {_{ {__     |  `.'  | {}  | {}  }
| { } | | .-._} }   | |\ /| | {}  | .-. \
`-' `-`-' `----'    `-' ` `-`----'`-' `-'
Enter the correct password to unlock the Operating System
[HFS_MBR]>
```

### Set up environment
The task here is to find the password to unlock the OS. Although there are instructions in *README* on how to setup IDA for reversing this program, I used GHIDRA for this challenge.

When importing *dos.img* into GHIDRA, it will not be able to recognize the file format. We can import it as a raw binary and set the processor to be x86 in 16-bit real mode. Before importing the file, also go to options and set the base address to be `0000:7c00` because 0x7c00 is where the bootloader starts.

To debug this in `GDB`, we can do `./run debug` to tell `QEMU` to run a gdbserver. In `GDB`, we can run the following commands to prepare the environment.

```
(gdb) target remote localhost:1234
Remote debugging using localhost:1234
(gdb) set architecture i8086
The target architecture is assumed to be i8086
(gdb) break *0x7c00
Breakpoint 1 at 0x7c00
```

Notice the `-s` and `-S` flags passed to `QEMU` when using `./run debug`. `-s` is for starting a `gdbserver` at port 1234, while `-S` is for `QEMU` to freeze CPU at startup, only starting execution after entering `c` (continue) in GDB.

Although I normally like to use GEF with `GDB`, but because `gef-remote` does not properly support x86 architectures at this point, I used this [gdbinit] script I found that is made to support real mode with `QEMU`. 

This [blog](http://ternet.fr/gdb_real_mode.html) explains some things about debugging programs running in real mode and under `QEMU`.

### Analyse the program
Similar to syscalls in our typical programs, the program uses interrupts `int 0x10`, `int 0x13`, `int 0x16` for interacting with the user.

* `int 0x10` - For reading/writing from/to the screen (https://en.wikipedia.org/wiki/INT_10H)
* `int 0x13` - For disk read/write (https://en.wikipedia.org/wiki/INT_13H)
* `int 0x16` - For control of the keyboard (https://en.wikipedia.org/wiki/INT_16H)

At the start, the program does some initial setup like setting the video mode. They aren't very important so I'll omit those. The first important part is 

``` 
0000:7c21 b8 02 02        MOV        AX,0x202
0000:7c24 b9 04 00        MOV        CX,0x4
0000:7c27 30 f6           XOR        DH,DH
0000:7c29 b2 80           MOV        DL,0x80
0000:7c2b bb 00 7e        MOV        BX,0x7e00
0000:7c2e cd 13           INT        0x13
0000:7c30 ff e3           JMP        BX
```

The program sets up the registers for interrupt call `0x13`. Referring to the [documentation](https://en.wikipedia.org/wiki/INT_13H#INT_13h_AH=02h:_Read_Sectors_From_Drive), based on the CHS (cylinder-head-sector) addressing scheme, this will be reading 2 sectors at CHS (0, 0, 4) from drive into address `0x7e00`. Then, the program jumps to `0x7e00`.

This [formula](https://en.wikipedia.org/wiki/Logical_block_addressing#CHS_conversion) describes how to convert between CHS to LBA (a linear addressing scheme), which will tell us that the program is reading from the 4th sector (each sector is 512 bytes).

We can copy this part into a separate file using `dd`.

```
dd if=dos.img of=part2 skip=3 obs=512 count=2`
```

(`obs=512` is to say each block to copy is 512 bytes, `skip=3` because we want to start copying from the 4th block, and `count=2` to copy 2 blocks)'

Another way to obtain the loaded code is by setting a breakpoint in `GDB` at `0x7c30` (just after the interrupt call), then dump the memory in `0x7e00`.

```
dump memory part2 0x7e00 0x8200
```

### Reverse the password checking code
Since the code is from the same file, we can just scroll down to address `0x8000` to analyse it. However, it would be better to load the file dumped earlier (*file1* or *file2*), and set the base address to `0x7e00` instead, to avoid missing any references and debugging would be easier knowing the exact addresses.

Now, we can see the code where the program tells us its loading and prompts for a password. Following which, it reads the password from our keyboard and checks if it is correct.

```
0000:7e37 b7 01           MOV        BH,0x1
0000:7e39 b4 00           MOV        AH,0x0
0000:7e3b cd 16           INT        0x16

0000:7e3d 3c 61           CMP        AL,'a'
0000:7e3f 0f 8c c1 01     JL         die
0000:7e43 3c 7a           CMP        AL,'z'
0000:7e45 0f 8f bb 01     JG         die
0000:7e49 b4 0e           MOV        AH,0xe
0000:7e4b cd 10           INT        0x10
```

The first interrupt call `int 0x16` will read one character from the keyboard, and save it in `ah`. Then, the program checks if it is within the range of lowercase letters. If outside the range, the program exits as the password is wrong, otherwise writes the character to the screen.

```
0000:7e4d 30 e4           XOR        AH,AH
0000:7e4f 88 c2           MOV        DL,AL

0000:7e51 2c 61           SUB        AL,0x61
0000:7e53 d0 e0           SHL        AL,1

0000:7e55 31 db           XOR        BX,BX
0000:7e57 88 c3           MOV        BL,AL
0000:7e59 b8 26 80        MOV        AX,0x8026
0000:7e5c 01 c3           ADD        BX,AX
0000:7e5e 8b 07           MOV        AX,word ptr [BX]
0000:7e60 ff e0           JMP        AX
```

After that, the provided character will be used as an index for a jump table located at `0x8026`. So each input character is handled differently.

This part is fairly trivial at this point, the check is performed by xoring the current position of the input with the input character. The following are the requirements of the password.

```
index ^ 'e' == 0x62 => 7
index ^ 'j' == 0x68 => 2
index ^ 'n' == 0x68 => 6
index ^ 'o' == 0x6e => 1
index ^ 'p' == 0x74 => 4
index ^ 'r' == 0x7a => 8
index ^ 's' == 0x73 => 0
index ^ 'u' == 0x76 => 3
index ^ 'w' == 0x72 => 5
```

From this, we can recover the password, `sojupwner`.


Send this to the challenge server, and we get

```
[HFS SECURE SHELL] Here is your flag for HFS-MBR: midnight{w0ah_Sh!t_jU5t_g0t_RE
ALmode}
[HFS SECURE SHELL] loaded at 100f:0100 (0x101f0) and ready for some binary carna
ge!
```

Onward to [part 2][part2], pwning the OS to read FLAG2.

---

Feel free to ask anything in the comments.

[download]:{{site.baseurl}}/ctfs/midnight-sun-quals-19/hfs-mbr/hfs-os.tar.gz
[part2]:{{site.baseurl}}/ctfs/midnight-sun-quals-19/hfs-dos/hfs-dos
[gdbinit]:{{site.baseurl}}/ctfs/midnight-sun-quals-19/hfs-mbr/gdbinit