---
layout: post
title: Teaser Dragon CTF 2018 - Chains of Trust (re391)
---

> Yet another reverse engineering challenge.
>
> P.S. It was tested on Ubuntu 17.10

As the binary connects to a server, follow the instructions [here](https://ctftime.org/task/6716) to set up the challenge locally. The intended solution is also attached by the challenge author there.

This was a really interesting challenge. Thank you so much [@gynvael](https://twitter.com/gynvael) for making this.

Before I start, small disclaimer: this is going to be a really long writeup. It is long because I will discuss about the techniques I used to approach difficulties faced in this challenge and my thought process. I also attached relevant pseudocode so that everyone can follow along, as I believe context is important.

All resources for this writeup can be downloaded [here](https://github.com/daniellimws/daniellimws.github.io/tree/master/ctfs/teaser-dragon-ctf-18/chains_of_trust).

## Challenge Overview
We are given a zip file, containing some libraries, a binary, and a script to run the file.

```sh
$ ll
total 5.7M
-rwxrwxrwx 1 1000 staff  19K Sep 26 16:38 chains
-rwxrwxrwx 1 1000 staff  189 Sep 26 16:27 go.sh
-rwxrwxrwx 1 1000 staff 167K Sep 26 13:23 ld-linux-x86-64.so.2
-rwxrwxrwx 1 1000 staff 1.9M Sep 26 13:23 libc.so.6
-rwxrwxrwx 1 1000 staff  15K Sep 26 13:23 libdl.so.2
-rwxrwxrwx 1 1000 staff  91K Sep 26 13:23 libgcc_s.so.1
-rwxrwxrwx 1 1000 staff 1.4M Sep 26 13:23 libm.so.6
-rwxrwxrwx 1 1000 staff 454K Sep 26 13:31 libpcre.so.3.13.3
-rwxrwxrwx 1 1000 staff 142K Sep 26 13:23 libpthread.so.0
-rwxrwxrwx 1 1000 staff 1.6M Sep 26 13:23 libstdc++.so.6
-rwxrwxrwx 1 1000 staff  119 Sep 26 17:04 README.txt
```

In the README, 

```
Run ./go.sh
If it doesn't seem to work, retry on Ubuntu 17.10 (but you do have to use ./go.sh).

Task: Find the flag.
```

As I was using a Ubuntu 16.04 docker image for my usual ctf stuff, it did not work on that machine. So I had to build a Ubuntu 17.10 image with my tools. You can get it with 

```
docker pull daniellim/ctftools1710
```

or clone this [repo](https://github.com/daniellimws/ctftools1710) that contains PowerShell scripts to manage the image.

There was nothing that stands out in `go.sh`, which just ensures that we are running the binary with the provided libraries. Either to make sure it works for everyone, or maybe they patched the libraries 🤔.

```sh
#!/bin/bash
# Default Ubuntu 17.10 environment (if it doesn't work, get Ubuntu 17.10).
chmod a+x ./ld-linux-x86-64.so.2
chmod a+x ./chains
./ld-linux-x86-64.so.2 --library-path . ./chains
```

Running `go.sh` runs the `chains` binary, which first checks for the required libraries, then gives us the following interface to enter a password (typical high tech interface by gynvael).

```sh
$ ./go.sh
Welcome to Chains.
Connecting to master...OK
Checking required libraries...
  + libc.so.6
  + libpthread.so.0
Looks good so far, but will do some more checks.
This might take a moment...
```

![main_screenshot][main_screenshot]

### Summary
This challenge could be splitted into multiple parts. 

Firstly, the main binary (I call it the driver) connects to a server and in a loop, reads shellcode from the server and `mmap`s a `RWX` region to store the code and execute it.

There were different types of shellcode:
* Check libraries
* Proof of work
* Anti-debug
* Actual program that asks and checks for the password, which was splitted into multiple pieces of code that spawns a thread each, so that all of them run concurrently (somewhat).

Lastly, amongst the threads that are spawned, there were also different types:
* **Main Menu** - Prints the cool menu and reads the password
* **Database** - A place to store data. Each entry is a `short` (2 bytes). There were 4 of this.
* **Distributer** - Takes the 32 bytes of input read, and splits them to store 8 bytes in each database.
* **Processor** - Retrieves the 8 bytes from the database, performs a simple operation to each of them, and stores it back. At this point, they are a `short` (no longer just a byte). There were also 4 of this, each one bound to a database.
* **Merger** - Retrieves in total 32 `short`s from the 4 databases, performs a simple operation to each of them, and stores all of them into one database.
* **Validator** - Retrieves the 32 `short`s, run each of them through some sort of hashing algorithm, and compares the result with a precomputed table.
* **Sleeping** - Does nothing but sleep. Just like you!

Here's a table of contents for easy reference:
- [**Driver**](#driver)
- [**Shellcodes**](#shellcodes)
- [**Threads**](#threads)
- [**Solution**](#solution)

Or, skip to the techniques used:
- [Automated code dumping](#automated-dumping)
- [Using dynamic analysis to find relationships between threads](#link-everything-together)

## Driver
This part was pretty straightforward. The program opens a socket connection to the server, and stores the file descriptor in a global variable for future use. Then, in a loop, it reads shellcode from the server, stores it in an executable memory region, and runs it.

*If you are not familiar with sockets in C, here's a pretty good [reference](https://beej.us/guide/bgnet/html/multi/syscalls.html).*

```c
int actual_main(char* master_host)
{
  init_functions_table();
  puts("Welcome to Chains.");
  printf("Connecting to master...");
  fflush(stdout);

  // create socket
  init_socket_struct(&socket_struct);
  if (connect_socket(&socket_struct, master_host, 7679u) ^ 1)
  {
    puts("FAILED");
  }
  else
  {
    puts("OK");
    // read 1 byte from socket
    read_n_from_socket(&socket_struct, &mysterious_byte, 1);
    global_socket_struct = &socket_struct;

    while ( we_done != 1 )
    {
      shellcode_len = 0;

      // reads 4 bytes as the length of the buffer to be read later
      if (read_n_from_socket(&socket_struct, &shellcode_len, 4) != 4)
      {
        fwrite("Master disconnected (timeout?)\n", 1uLL, 31uLL, stderr);
        break;
      }

      // some mmap stuff, trying to page align
      len = (shellcode_len + 4095LL) & 0xFFFFFFFFFFFFF000LL;
      addr = mmap(0LL, len, 7, 34, -1, 0LL); // mmap(0, len, RWX, 34, -1, 0)
      if (!addr)
      {
        fwrite("mmap failed, this should not happen unless you're doing sth weird.\n", 1uLL, 0x43uLL, stderr);
        break;
      }

      // reads a buffer of length indicated earlier
      if (read_n_from_socket(&socket_struct, addr, shellcode_len) != shellcode_len)
      {
        fwrite("Master disconnected (timeout?)\n", 1uLL, 0x1FuLL, stderr);
        break;
      }

      // running the shellcode
      mysterious_byte = (*addr)(&functions_table, mysterious_byte);
      munmap(addr, len);
    }
  }
}
```

The exact implementation of how the program interacts with the server was not so important. The significant thing here are the 2 parameters being passed into the shellcode, namely the `functions_table` and a `mysterious_byte`.

The `functions_table` was initiated earlier in `init_functions_table()`. This seems to provide the shellcode more capability than to merely run basic instructions.

```c
functions_table = [                             
    send_from_to_socket,            // 0x0   
    send_n_to_socket,               // 0x8      
    read_n_from_socket,             // 0x10     
    done_reading_shellcode,         // 0x18     
    puts,                           // 0x20     
    printf,                         // 0x28     
    read_n_minus_one_from_stdin,    // 0x30     
    fflush_stdout,                  // 0x38     
    exit,                           // 0x40     
    mmap_size_perms,                // 0x48     
    sleep_millis,                   // 0x50     
    pthread_create,                 // 0x58     
    dlsym,                          // 0x60     
    dlopen,                         // 0x68     
    dlclose                         // 0x70     
]                                               
```

On the other hand, `mysterious_byte` was read in at the very start, passed in to the shellcode, then replaced with the return value. At first, I thought this was going to be the flag. However, it is random every time and did not serve much purpose, but just something like a proof of work, maybe to prevent automation, or perhaps to check if the connection is still alive.

Now that this is clear, the next logical step is to retrieve these shellcodes and analyse them.

## Shellcodes
My first approach to this was to just set a breakpoint in gef, then dump the memory in the `mmap`ed region into a file. And this is what I get

```c
int main()
{
  enc = (char*) 0x66;  // address of the encrypted code
  // decrypt the code
  for (int i = 0; i < 4096; ++i)
  {    
    enc[i] = __ROR1__(
              __ROL1__(
                (__ROR1__(__ROR1__(__ROR1__(((((((enc[i] ^ 0x39) + 59) ^ 0xD3) + 25) ^ 0xA8) + 105) ^ 0xF6, 7), 4), 6) - 118) ^ 0xEC,
                5),
              1);
  }

  res = (*enc)();    // run the decrypted code
  memset(enc, 0, 0x1000);
  return res;
}
```

Troublesome... Self-decrypting code... I can either emulate this code using unicorn, or do what I did, which was just set a deeper breakpoint at the end of the decryption, then dump the decrypted memory.

At this point, looking at Hex-Rays pseudocode was no longer feasible, because the code uses functions from the `functions_table`, and all the definitions of these functions are not present in the binary. So obviously, Hex-Rays would only be able to interpret it as retrieving a function pointer and calling this function.

Regardless, here's the pseudocode for the unpacked/decrypted binary.

```c
char main(void* functions_table[], char mysterious_byte) {
    check_library(functions_table);

    // proof of work
    read_n_from_socket(&c, 1);
    mysterious_byte *= 5;
    mysterious_byte += c;
    send_1_to_socket(mysterious_byte);
    return mysterious_byte;
}

int check_library(void* functions_table[])
{
  puts("Checking required libraries...")  
  libraries = ["libc.so.6", "libpthread.so.0"];
  for (int i = 0; i < 2; ++i)
  {
    if (!dlopen(libraries[i]))
    {
      printf("Missing required library: %s\n", libraries[i]);
      exit(0);
    }
  }
  puts("Looks good so far blah blah")
}
```

Now we know how the subsequent `mysterious_byte`s are generated. At this point, several thoughts came to mind.

Maybe this `mysterious_byte` is used as verification to obtain the next piece of code from the server. I quickly wrote a short Python script to test this theory, but it seems like even by sending random bytes over, I still get the next piece of code. So, I am almost certain that it is just to check if the connection is still alive/keep the connection alive.

Or, maybe the flag is the concatenation of all `mysterious_byte`s. Again, using a short Python script, I tested and realized the `mysterious_byte` is always different, so unlikely to be the flag. (Gynvael is not so kind 😛)

Again, more thoughts came to mind, maybe it has something to do with the arithmetic being performed on the byte, etc. But enough speculation, more action. I should dump the subsequent pieces of code to find out.

### Automated Dumping
Clearly, we must automate the dumping process, since who knows how many more pieces of code there are. Also, if we do it by hand, we need to be super fast, or the connection to the server will timeout.

My first thought was to use the GDB script I wrote earlier for the CTF last week ([writeup](https://daniellimws.github.io/DCTF18-memsome.html)). Through this, I will automate finding the address of the `mmap`ed region in the **driver**, set a breakpoint at when the decryption is done, then dump the decrypted code. Simple.

However, there's a catch. It seems that Gynvael foresaw this coming. For every piece of code read from the server, there are random number of `nop` instructions in it, i.e. the address offset for when the decryption is done is not constant and the method mentioned above will fail.

I needed a way to calculate the offset before dumping. 😢

#### Scripting with GEF
Scripting GDB is not powerful enough. I want to directly access the memory and look for a specific instruction, so that I know where to set the breakpoint. 

I decided to leverage the Python API for GDB, and write a command to do this 😛. In particular, I am using GDB with GEF, so I am able to use the nice wrapper functions from GEF.

Now, what I am looking for is the first `mov rdx, rax` instruction (I've made sure this is the first instance of this instruction), and get the address of `call some_offset` which is the instruction before it.

![packed call screenshot][packed_call_screenshot]

The reason I used `mov rdx, rax` is because there are 3 bytes for the opcodes of this instruction (`48 89 d0`), instead of `call` that has only one constant byte, and last 4 bytes are the relative offset of the address (`e8 00 00 00 00`). `e8` could have just been one of the values used to decrypt the code, and I don't want to risk it.

With this, I came up with a `break-and-dump` command. (The following code only works when GEF is loaded)

```py
class DumpBreakpoint(gdb.Breakpoint):
    """Temporary breakpoint to dump unpacked shellcode"""

    def __init__(self, location):
        super(DumpBreakpoint, self).__init__(location, gdb.BP_BREAKPOINT, internal=True, temporary=True)
        self.silent = True
        return

    def stop(self):
        return True
```

```py
class BreakAndDumpCommand(GenericCommand):
    """Finds the call instruction in the shellcode binary, and sets a temporary breakpoint on it.
    Then, we can dump the 0x1000 bytes in the mmaped region
    """
    _cmdline_ = "break-and-dump"
    _syntax_  = "{} NAME".format(_cmdline_)

    def do_invoke(self, args):
        disable_context()

        number = gdb.parse_and_eval(args[0])    # break-and-dump NUMBER
        name = "unpacked{}.dump".format(number)
        open("log", "a").write("{}: ".format(name))

        # address of mmaped region
        start_address = read_int_from_memory(get_register("rsp") + 0x20)
        mmap_memory = bytes(read_memory(start_address, 0x1000))

        addr = self.find_call_instruction(mmap_memory) + start_address

        # now we execute the binary to the point where the code just finished unpacking
        DumpBreakpoint("*{:s}".format(hex(addr)))
        gdb.execute("c")

        if addr == None:
            err("GG can't find the call instruction. This shellcode must be different from the previous ones.")

        # code is unpacked, now dump it
        # call offset jumps to the instruction (address of next instruction + offset)
        unpacked_address = addr + 5  # call offset -> E8 offset 00 00 00
        unpacked_address += read_memory(addr + 1, 1)[0]  # next insn address + offset
        info("Unpacked code is under {:s}".format(hex(unpacked_address)))

        gdb.execute("dump memory {} {} {}".format(name, hex(unpacked_address),
                                                  hex(start_address + 0x1000)))
        info("Dumped unpacked code to {}".format(name))

        # continue executing til the end of the function (don't step into decrypted code)
        # multiple ni because gdb seems to screw up when doing finish straight away
        gdb.execute("ni")
        gdb.execute("ni")
        gdb.execute("ni")
        gdb.execute("ni")

        gdb.execute("finish")
        return

    def find_call_instruction(self, memory):
        """Searches for the instruction that calls the unpacked code"""

        # first, we need to search for the first `mov rdx, rax`, because `call` has only 
        # one constant byte in its opcode, and it is not reliable to search for it
        opcode = b"\x48\x89\xc2"
        last_found = -1  # Begin at -1 so the next position to search from is 0
        while True:
            # Find next index of opcode, by starting after its last known position
            last_found = memory.find(opcode, last_found + 1)
            if last_found == -1:
                break  # All occurrences have been found

            # minus 5 because `call` opcode has 5 bytes, 
            # and we want the address of `call` which is before `mov rdx, rax`
            return last_found - 5  

        return None
```

What this command does is:
1. Retrieves the address of the `mmap`ed region from the stack
2. Searches for the `call` instruction, and sets a temporary breakpoint
3. Calculates the address of the decrypted code, and dumps it into a file

Now that I have a reliable way to dump the decrypted code, I scripted GDB to dump a couple more pieces of code to analyse.

```
gef config context.enable 0

source breakpointscript.py

pie break *0x1806
pie run

set $i = 0

while ($i < 0x10)
    break-and-dump $i
    c
    set $i++
    end

gef config context.enable 1

p "[+] Done dumping shellcodes"
```

I dumped 16 pieces of code in my first run. The cool interface had not yet shown up, but I got a message saying `"No debugging, go away!"`. Man... there's also anti-debugging code...

### Useless Code
I continued by looking at the dumped code one by one. The first few were of the following structure.

```c
char main(void* functions_table[], char pow_byte) {
    char s[4];
    send_n_to_socket("WoRK", 4);
    read_n_from_socket(s, 4);
    // does some arithmetic to the 4 bytes and pow_byte, then store into pow_byte
    // it is different every time
    send_1_to_socket(pow_byte)
    return pow_byte
}
```

I just classified this as useless code. Since my theory based on everything I found earlier was that this proof of work byte was useless. But I still kept in mind that this exists since it could be related to the flag in the end.

To avoid wasting time, I added a logging functionality to my command, so that I can tell whether this is a fresh piece of code.

```py
mmap_memory = bytes(read_memory(start_address, 0x1000))
open("log", "a").write("{}: ".format(name))
if b"WoRK" in mmap_memory:
    info("Useless code!")
    open("log", "a").write("Useless code!\n")
else:
    info("Fresh code")
    open("log", "a").write("--- Fresh code! ---\n")
```

Run my GDB script one more time, and I identified which code was useless, and avoided those.

```
unpacked0x0.dump: --- Fresh code! ---  (Check required libraries)
unpacked0x1.dump: Useless code!        
unpacked0x2.dump: Useless code!        
unpacked0x3.dump: Useless code!        
unpacked0x4.dump: Useless code!        
unpacked0x5.dump: Useless code!        
unpacked0x6.dump: Useless code!        
unpacked0x7.dump: Useless code!        
unpacked0x8.dump: Useless code!        
unpacked0x9.dump: Useless code!        
unpacked0xa.dump: Useless code!        
unpacked0xb.dump: --- Fresh code! ---  
unpacked0xc.dump: Useless code!        
unpacked0xd.dump: Useless code!        
unpacked0xe.dump: --- Fresh code! ---  
unpacked0xf.dump: --- Fresh code! ---   
```

### Anti-Debugging
These fresh pieces of code were variants of anti-debugging code. They were random so I had to deal with all of them. But it's one of the following:
* Checking if `ptrace` returns -1
* Checking if `errno` returns 0
* Uses `readlink` to get the name of the running process, and uses `strstr` to check if `"/gdb"` is part of it
* Checks if `LD_PRELOAD` was used
* Uses `getppid` to get the parent pid and check if this is a child process

I was so impressed looking at the implementation of this. In order to get access to libc functions that weren't in `functions_table`, Gynvael used `dlsym` (which is present in `functions_table`) to resolve the addresses of the functions he wants. Crazy!

#### Patching while dumping
Since I already have code to dump the decrypted code, I thought, why not also let it patch out parts of code that tries to end my program.

And crazy as it sounds, it was the most convenient method for me, so I did it.

```py
decrypted_code = bytes(read_memory(start_address, 0x1000))

# program checks strstr(process_name, "/gdb") == 0
# replace strstr with atoi to bypass anti-debug
decrypted_code = decrypted_code.replace(b"strstr", b"atoi\x00\x00")

# program checks if errno == 1
# replacing `mov rax,QWORD PTR [rbp-0x10]; mov eax,DWORD PTR [rax]`
# with `mov eax, 0x1; nop`
if b"errno" in decrypted_code:
    decrypted_code = decrypted_code.replace(b"\x48\x8B\x45\xF0\x8B\x00", b"\xb8\x01\x00\x00\x00\x90")

# checking if ptrace returns -1
# replacing `cmp rax, 0xffffffffffffffff`
# with `test rax, rax; nop`
if b"ptrace" in decrypted_code:
    decrypted_code = decrypted_code.replace(b"\x48\x83\xf8\xff", b"\x48\x85\xc0\x90")

# yes, only these few got triggered so I didn't touch the rest
# ok just override the memory
write_memory(start_address, decrypted_code, 0x1000)
```

With this in place, I was able to bypass all the anti-debugging code. I also added code for the logging to detect the string `"No debugging"`.

Time to dump more code!

### Main Menu
```
unpacked0x17.dump: --- Fresh code! ---
```
The `0x17`th piece of code finally showed the sweet interface for me to enter the password.

The program `mmap`s a `RW` region, probably to store some information, and sends the address to the server.

After that, it does some fancy arithmetic to calculate the address of this code in the **driver**, as well as the number of bytes of code this program actually has. Then, it copies the code of this program to another `RWX` `mmap`ed region (since this will be replaced later with the next retrieved code). Then, it spawns a thread running a function in the new `mmap`ed region. 😱 

```c
char main_menu(void* functions_table[]) {
    addr1 = mmap_wrapper(0x150, RW);
    *(addr1 + 8) = 0;
    *(addr1 + 9) = 0;
    *(addr1 + 10) = 0;
    send_n_to_socket(addr1, 8);

    addr2 = mmap_wrapper(size_of_this_binary, RWX)
    memcpy(addr2, address_of_this_code_in_memory, size_of_this_binary)

    thread_function_addr = &thread_function - address_of_this_code_in_memory + addr2;

    pthread_create(&pthread_struct, thread_function_addr, addr1);
}
```

Another insane move by Gynvael!

The function loaded in the thread just prints the fancy interface, reads 32 bytes from the user, waits for something, and prints out something.

```c
// this is addr1 from previous
char main_menu_thread(char* arg) {
    print_fancy_ui();
    read_n_bytes_from_stdin(32);

    arg[9] = 1;

    while(true) {
        if (arg[8])
            break;
        if (arg[10]) {
            puts(*(arg + 0x4B));
        }

        mfence

        arg[10] = 0
        sleep();
    }
}
```

What is `*(arg+0x4B)`? When is `*(arg+0x8)` or `*(arg+0x10)` modified? No idea. This got me stuck for a while, but in the end I came up with the hypothesis that since earlier, the `mmap`ed address (`arg`) was sent to the server, there would be more threads being spawned after this, and the server will tell them this address.

#### mfence
If you are unfamiliar with `mfence`, it is used to indicate that all instructions before this line must be executed before all instructions after this line. Huh? What am I saying? Isn't this obvious?

As we know, each line of code in C corresponds to multiple instructions in Assembly. The CPU implements pipelining such that multiple instructions that do not conflict with each other will run concurrently.

Often in multithreaded applications, to avoid race conditions, where different threads access the same memory region at the same time, `mfence` will be used together with mutexes to prevent unexpected behaviour.

More information could be found [here](https://www.geeksforgeeks.org/process-synchronization-set-1/).

### Sleeping code
After the main menu, there came another piece of useless code. This one just `sleep`s for a small duration.

Unfortunately, because there are not even any unique strings in this program, I couldn't add any code to detect it in the future dumps. Anyways, it was fine since this was the only occurence.

### More threads
Dumping more code, I got a total of 12 threads (including the main menu). I believed all of these are responsible in validating the flag, so I started to reverse them one by one.

Since this is so long, it deserves a section of its own. 😛

### More sleeping code
Just now I said that was the only occurence of the sleeping code. I lied. After the validation thread, the server just sends some more code for the **driver** to sleep so that the program does not terminate. (Of course, there is still a limit)

## Threads
All the code here follow the same pattern as the main menu:
1. `mmap` a `RW` region, and send its address to the server
2. `mmap` another `RWX` region, and copy the entire contents of this small program into it
3. Calculates the new address of the function for the thread to load
4. Runs the thread with the first `mmap`ed address as argument

Except there's an extra step. Populate the `RW` region with addresses retrieved from the server. My hypothesis earlier was correct!

Now, let's look at the different types of threads received.

### Database
```
unpacked0x22.dump: --- Fresh code! ---
unpacked0x23.dump: --- Fresh code! ---
unpacked0x24.dump: --- Fresh code! ---
unpacked0x25.dump: --- Fresh code! ---
```

There were 4 of this that does exactly the same thing.

```c
void database_thread(char* arg) {
    short buffer[128] = arg + 0x0A + 32;
    for (int i = 0; i < 128; ++i)
        buffer[i] = 0;
        
    while(true) {
        if (!arg[8])
            break;
        
        for (int i = 0; i < 3; ++i) {
            slot* slt = arg + 0x0A + i * 8;

            if (!slt.is_set) {
                index = slt.index;
                slt.value = buffer[index];
                mfence
                slt[5] = 1;
            }
            else {
                index = slt.index;
                buffer[index] = slt.value;
            }
            mfence
            slt.processing = 0;
            mfence
        }
    }
}
```

As seen here, the database has a storage space of 128 shorts. Other threads can either get or set values by modifying the `slot`. There are 4 `slot`s for each database, and they have the following structure.

```c
struct slot {
    short index,
    short value,
    bool processing,
    bool done_get,
    bool is_set
}
```

#### Getter and Setter
In the following threads, all of them will have these 2 functions:

```c
short get_value(short index, slot* database_slot)
{
  database_slot.done_set = 0;
  database_slot.is_set = 0;
  database_slot.index = index;
  mfence
  database_slot.done_get = 1;
  mfence
  while (!database_slot.done_get)
    sleep();
  mfence
  return database_slot.value;
}
```

```c
short set_value(short index, short value, slot* database_slot)
{
  database_slot.done_set = 0;
  database_slot.is_set = 1;
  database_slot.value = value;
  database_slot.index = index;
  mfence
  database_slot.processing = 1;
  mfence
  while (database_slot.processing)
    sleep();
  mfence
  return database_slot.value;
}
```

Pretty straightforward, just get or set values in a database given an index, with some checks and a few `mfence`s to ensure no race conditon.

### Processor
```
unpacked0x31.dump: --- Fresh code! ---
unpacked0x32.dump: --- Fresh code! ---
unpacked0x33.dump: --- Fresh code! ---
unpacked0x34.dump: --- Fresh code! ---
```

Following the database, I got 4 more threads that look identical. Each of them sleeps until the value under index 32 in the database is set to `1`. After that, it reads 8 values from the database and performs some arithmetic, then stores them back. Finally, it pushes the value `1` into index 33.

```c
void processor_thread(char* arg)
{
  slot* slt = *(arg + 0x10);

  while (!arg[8] && !get_value(32, slt)
    sleep();

  for (index = 0; index < 8; ++index)
  {
    value = get_value(index, slt);
    num = arg[9]
    switch (num) {
    case 0:
      value *= 123;
      break;
    case 1:
      value += index_1 + 20384;
      break;
    case 2:
      value ^= 0x73ABu;
      break;
    case 3:
      value += 9981;
      break;
    }
    push_value(index, value, slt);
  }
  return push_value(33, 1, slt);
}
``` 

As you can see the behaviour of the thread is determined by the value in `arg[9]`. Before creating the thread (code not shown here), the program initializes `arg[9]` with a unique value from 0-3, i.e. 4 of the processor threads performs different operations.

### Distributer
```
unpacked0x3f.dump: --- Fresh code! ---
```

This thread, as its name suggests, distributes the 32 byte input into 4 different databases.

```c
void distributer_thread(char* arg)
{
  while (!arg[8] && !arg[9])
    sleep();

  char* other_arg = *(arg + 0x10)
  while (!arg[8] && !*(other_arg + 9))
    sleep();

  char* user_input = *(arg + 0x10) + 0xB;
  slot* slots = arg + 0x18;
  for (i = 0; i < 32; ++i)
    set_value(i / 4, user_input[i], slots[i % 4]);
  for (j = 0; j < 4; ++j)
    set_value(32, 1, slots[j]);
  for (k = 0; k < 4; ++k)
  {
    while (!*(arg + 8) && !get_seed(33, slots[k]))
      sleep();
  }

  arg[10] = 1;
  arg[8] = 1;
}
```

As you can see, after distributing the user input, it sets value 1 to index 32 for each database. After that, it waits for the value under index 33 to be set to 1.

It looks like this happens before the processor threads.

### Merger
```
unpacked0x4a.dump: --- Fresh code! ---
```

This thread takes in 8 shorts from 4 different databases each, xors them with `0x6666` and saves them all into 1 database at index `i+64`.

```c
void merger_thread(char* arg)
{
  while (!arg[8] && !arg[9])
    sleep();

  char* other_arg = *(arg + 0x10)
  other_arg[9] = 1;

  while (!arg[8] && !*(other_arg[10]) )
    sleep();

  slot* slots = arg + 0x18;
  for (index = 0; index < 32; ++index)
  {
    value = get_value(index % 8, slots[index / 8]);
    // everything is stored in the last slot
    send_value(index + 64, seed ^ 0x6666, slots[3]);
  }
  arg[10] = 1;
  arg[8] = 1;
}
```

### Validator
```
unpacked0x55.dump: --- Fresh code! ---
```

The validator takes out values at index `i+64`, use each of them to generate a hash, and compares it with a target. The exact details of the hashing algorithm won't be discussed here since it is not related to the flow of the program.

```c
void validator_thread(char* arg)
{
  char* other_arg1 = *(arg + 0x18)
  other_arg1[9] = 1;
  mfence
  while (arg[8] && !other_arg1[10])
    sleep();

  target_hash[0] = some_address0;
  target_hash[1] = some_address1;
  target_hash[2] = some_address2;
  target_hash[3] = some_address3;
  // truncated because too long. there are 32 in total

  correct_or_not = 0;
  slot* slt = *(arg + 0x38);
  for (i = 0; i < 32; ++i)
  {
    seed = get_value(index + 64, slt);
    generate_hash(seed, hash_result);
    for (j = 0; j < 32; ++j )
      correct_or_not |= target_hash[i][j] ^ hash_result[index2];
  }

  char* other_arg2 = *(arg + 0x10);
  if (correct_or_not)
    strcpy(other_arg2 + 0x4b, "No luck.");
  else
    strcpy(other_arg2 + 0x4b, "\x1B[38;5;46mYes! Well done!");

  mfence;

  other_arg2[10] = 1;
  other_arg2[8] = 1;
  arg[8] = 1;
  return exit();
}
```

Woah! There's a lot of information here. If you noticed, in some of the threads above, we have `other_arg` which is a reference to an `arg` of a different thread, and this information was obtained from the server. Some threads wait for a certain offset in the `other_arg` to be set, while some set values in a certain offset of an `other_arg`.

From this, we realize that each thread waits for another thread to be done, or when it is done goes on and notifies the thread that is supposed to run next.

### Link everything together
Now, we just need to find out what `other_arg` refers to for each thread. This is not possible through static analysis since the information is obtained from the server.

Some may find it obvious at this point, but of course this is due to having clear pseudocode. At the time of doing this challenge, I did not yet have such a clear understanding of what is going on, and had to retrieve the references to piece everything together.

#### Treasure hunt

To do this, I allowed my script to dump code up to the part where we finished loading the validator thread. At this point, all threads will be running, and I can inspect the `RW` `mmap`ed region (aka `arg`) of each thread.

First, I need to know at least the location of one of the `arg`s. There are many ways to do this. What I did was to provide an input, as I know that it will be stored in the `arg` of the main menu thread. Then, I just need to search for its location in memory.

```
gef➤  grep daniellim
[+] Searching 'daniellim' in memory
[+] In (0x7ffff0000000-0x7ffff0021000), permission=rw-
  0x7ffff0000b10 - 0x7ffff0000b30  →   "daniellimweesoongdaniellimweewee"
  0x7ffff0000b21 - 0x7ffff0000b30  →   "daniellimweewee"
[+] In (0x7ffff7ff5000-0x7ffff7ff6000), permission=rw-
  0x7ffff7ff500b - 0x7ffff7ff502b  →   "daniellimweesoongdaniellimweewee"
  0x7ffff7ff501c - 0x7ffff7ff502b  →   "daniellimweewee"
```

And find out the page that they reside in.

```
gef➤  xinfo 0x7ffff0000b10
─────────────────────────[ xinfo: 0x7ffff0000b10 ]─────────────────────────
Page: 0x00007ffff0000000  →  0x00007ffff0021000 (size=0x21000)
Permissions: rw-
Pathname:
Offset (from page): 0xb10
Inode: 0
gef➤  xinfo 0x7ffff7ff500b
─────────────────────────[ xinfo: 0x7ffff7ff500b ]─────────────────────────
Page: 0x00007ffff7ff5000  →  0x00007ffff7ff6000 (size=0x1000)
Permissions: rw-
Pathname:
Offset (from page): 0xb
Inode: 0
```

The first one is unlikely to be since the size of the page is really large. Looking at the `vmmap`, and searching for `0x00007ffff7ff5000`, I got a sense of where the `arg`s are.

```
0x00007ffff7fd7000 0x00007ffff7fd8000 0x0000000000000000 rwx                                    
0x00007ffff7fd8000 0x00007ffff7fd9000 0x0000000000000000 rw-                                    
0x00007ffff7fd9000 0x00007ffff7fda000 0x0000000000000000 rwx                                    
0x00007ffff7fda000 0x00007ffff7fdb000 0x0000000000000000 rw-                                    
0x00007ffff7fdb000 0x00007ffff7fdc000 0x0000000000000000 rwx                                    
0x00007ffff7fdc000 0x00007ffff7fdd000 0x0000000000000000 rw-                                    
0x00007ffff7fdd000 0x00007ffff7fde000 0x0000000000000000 rwx                                    
0x00007ffff7fde000 0x00007ffff7fdf000 0x0000000000000000 rw-                                    
0x00007ffff7fdf000 0x00007ffff7fe0000 0x0000000000000000 rwx                                    
0x00007ffff7fe0000 0x00007ffff7fe1000 0x0000000000000000 rw-                                    
0x00007ffff7fe1000 0x00007ffff7fe2000 0x0000000000000000 rwx                                    
0x00007ffff7fe2000 0x00007ffff7fe3000 0x0000000000000000 rw-                                    
0x00007ffff7fe3000 0x00007ffff7fe4000 0x0000000000000000 rwx                                    
0x00007ffff7fe4000 0x00007ffff7fe5000 0x0000000000000000 rw-                                    
0x00007ffff7fe5000 0x00007ffff7fe6000 0x0000000000000000 rwx                                    
0x00007ffff7fe6000 0x00007ffff7fee000 0x0000000000000000 rw-                                    
0x00007ffff7fee000 0x00007ffff7fef000 0x0000000000000000 rwx                                    
0x00007ffff7fef000 0x00007ffff7ff0000 0x0000000000000000 rw-                                    
0x00007ffff7ff0000 0x00007ffff7ff1000 0x0000000000000000 rwx                                    
0x00007ffff7ff1000 0x00007ffff7ff2000 0x0000000000000000 rw-                                    
0x00007ffff7ff2000 0x00007ffff7ff3000 0x0000000000000000 rwx                                    
0x00007ffff7ff3000 0x00007ffff7ff4000 0x0000000000000000 rw-                                    
0x00007ffff7ff4000 0x00007ffff7ff5000 0x0000000000000000 rwx                                    
0x00007ffff7ff5000 0x00007ffff7ff6000 0x0000000000000000 rw-                                  
```

The `RW` region should be the `arg` and the `RWX` region the copied code for the thread, and it starts from the bottom (the main menu thread is at the bottom, validation thread at the top).

Now, I just need to look at the `arg` of the validation thread, and see which other `arg`s does it reference to. The same goes for the others.

#### Find thread
To simplify this process, I wrote **another** GDB command to help me. This command will search for the `mmap`ed regions that match the code in a given file.

```py
class SearchMatchingThread(GenericCommand):
    """Finds the call instruction in the shellcode binary, and sets a temporary breakpoint on it.
    Then, we can dump the 0x1000 bytes in the mmaped region
    """
    _cmdline_ = "find-thread"
    _syntax_  = "{} NAME".format(_cmdline_)

    def do_invoke(self, args):
        if len(args) != 1:
            err(self._syntax_)
            return

        filename = args[0]
        contents = open(filename, "rb").read()[: 100]

        vmmap = get_process_maps()
        # get starting address to search because it is different every time
        start_addr = [x.page_start for x in vmmap if x.permission == 7][0]
        # get end address to search
        end_addr = [x.page_end for x in vmmap if x.permission == 7][-1]
        # read the memory between all RWX regions
        memory = read_memory(start_addr, end_addr - start_addr)
        # search for memories that match and print the information
        for i in self.find_memory(memory, contents):
            gdb.execute("xinfo {}".format(hex(i + start_addr)))


    def find_memory(self, memory, target):
        last_found = -1
        while True:
            last_found = memory.find(target, last_found + 1)
            if last_found == -1:
                break  # All occurrences have been found

            yield last_found
```

Now my workflow is simplified to something like the following:

```
gef➤  find-thread validation
─────────────────────────[ xinfo: 0x7ffff7fd7064 ]─────────────────────────
Page: 0x00007ffff7fd7000  →  0x00007ffff7fd8000 (size=0x1000)
Permissions: rwx
Pathname:
Offset (from page): 0x64
Inode: 0
```

The `arg` is in `0x00007ffff7fd8000`.

```
gef➤  telescope 0x00007ffff7fd8000
0x00007ffff7fd8000│+0x00: 0x0000555555758080  →  0x000055555555536a  →   push rbp
0x00007ffff7fd8008│+0x08: 0x0000000000000000
0x00007ffff7fd8010│+0x10: 0x00007ffff7ff5000  →  0x0000555555758080  →  0x000055555555536a  →   push rbp
0x00007ffff7fd8018│+0x18: 0x00007ffff7fda000  →  0x0000555555758080  →  0x000055555555536a  →   push rbp
0x00007ffff7fd8020│+0x20: 0x00007ffff7ff3022  →  0x0000000000000000
0x00007ffff7fd8028│+0x28: 0x00007ffff7ff1022  →  0x0000000000000000
0x00007ffff7fd8030│+0x30: 0x00007ffff7fef022  →  0x0000000000000000
0x00007ffff7fd8038│+0x38: 0x00007ffff7fe6022  →  0x0000000000000000
0x00007ffff7fd8040│+0x40: 0x0000000000000000
0x00007ffff7fd8048│+0x48: 0x0000000000000000
```

It contains a reference to `0x00007ffff7ff5000` and `0x00007ffff7fda000`. By trying out the files one by one (yea I was lazy to write another function for this), I realize `0x00007ffff7ff5000` is the `arg` for the main_menu thread.

```
gef➤  find-thread main_menu
─────────────────────────[ xinfo: 0x7ffff7ff4066 ]─────────────────────────
Page: 0x00007ffff7ff4000  →  0x00007ffff7ff5000 (size=0x1000)
Permissions: rwx
Pathname:
Offset (from page): 0x66
Inode: 0
```

We are almost there!

Putting everything we know together, the relationships are as follows:
* **Main Menu** - Waits for **Validator** to set the result message and notify it.
* **Database** - Does not care about anyone, just keep running.
* **Processor** - Each of this is connected to a **Database**. It will wait for **Distributor** to finish first, and notify it when it is done.
* **Distributor** - Notifies **Processor** when it is done, but wait for a response from **Processor**. Then, notifies **Merger** to start.
* **Merger** - Waits for **Distributor**. Notifies **Validator** when done.
* **Validator** - Waits for **Merger**. Notifies **Main Menu** when done.

For the **Distributor** and **Merger** which connect to 4 **Databases**, they each maintain an array of 4 `slot`s to connect to, and the ordering is the same for both threads. At the same time, the index of each `slot` in these 2 threads is the same as the number label for each **Processor** (the number that determines its behaviour).

With this in place, the program does the following:
1. Splits the user input into 4 databases
2. Process the values in each database differently
3. Combines values from all 4 databases into 1, while xoring each value with `0x6666` in the process.
4. Retrieve the values from the database, compute a hash, compare with target.

## Solution
Wow! You made it here!

The solution script merely does the following:
1. Brute force the corresponding seed value for each hash and put them in an array
2. Undo the merging step
3. Undo the processing step
4. Undo the distributing step
5. Get flag!

```py
def undo_processor_distributor(l):
    res = [0] * 32
    for i in range(32):
        c = l[i % 4][i // 4]
        if i % 4 == 1:
            c = c - (i // 4) - 20384
        if i % 4 == 2:
            c = c ^ 0x73AB
        if i % 4 == 3:
            c = c - 9981
        if i % 4 == 0:
            c = c // 123

        res[i] = c % 65536

    return res

def undo_merger(s):
    res = [ [0] * 8 for _ in range(4) ]
    for i in range(32):
        res[i // 8][i % 8] = s[i] ^ 0x6666

    return res

def generate_array(n):
    consts = [0x9DF9, 0x65E, 0x3B94, 0xFAD9, 0xC3D9, 0xFE12, 0xA57B, 0x9089, 0x3FAF, 0xBB31, 0x4CAD, 0x1415, 0x74CD, 0xCF0A, 0x1CE1, 0xB55A, 0x54C6, 0x827F, 0x179D, 0x66D9, 0xFF80, 0x8126, 0x5579, 0x4AED, 0x5F7D, 0x430F, 0x2EE4, 0x129C, 0xDBCD, 0xEB50, 0x8DA8, 0xBDD1]
    res = [0] * 32

    for i in range(32):
        m = ((n >> 1) | (n << 15)) % 65536
        n = m ^ consts[i]
        res[i] = n % 256

    return res

def brute_force(buf):
    for i in range(65536):
        if buf == generate_array(i):
            return i

def get_buffers():
    start_addresses = [0x8A0, 0x8C8, 0x8F0, 0x918, 0x940, 0x940, 0x940, 0x968, 0x990, 0x9B8, 0x9E0, 0xA08, 0xA08, 0xA30,  0xA58, 0xA80, 0xAA8, 0xAD0, 0xAF8, 0xB20, 0xB48, 0xB70, 0xB98, 0xB98, 0xBC0, 0xBE8, 0xC10, 0xC38,0xC60, 0xC10, 0xC88, 0xC88]

    mem = open("validation", "rb").read()
    res = []

    for i in range(32):
        start = start_addresses[i]
        res.append(list(mem[start: start+32]))

    return res

buffers = get_buffers()

nums = []
for i in range(32):
    nums.append(brute_force(buffers[i]))

nums = undo_merger(nums)
flag = undo_processor_distributor(nums)
flag = ''.join(map(chr, flag))
print(flag)
```

<iframe width="560" height="315" src="https://www.youtube.com/embed/annAZbwSDXE?rel=0&amp;controls=0&amp;showinfo=0&mute=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

All resources can be downloaded [here](https://github.com/daniellimws/daniellimws.github.io/tree/master/ctfs/teaser-dragon-ctf-18/chains_of_trust).

Once again, I would like to thank Gynvael for this challenge, and thank you for reading until the end.

[main_screenshot]:{{site.baseurl}}/ctfs/teaser-dragon-ctf-18/chains_of_trust/images/main.png
[packed_call_screenshot]:{{site.baseurl}}/ctfs/teaser-dragon-ctf-18/chains_of_trust/images/packed_call.png