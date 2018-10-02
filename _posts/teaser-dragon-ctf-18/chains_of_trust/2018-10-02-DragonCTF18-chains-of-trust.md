---
layout: post
title: Teaser Dragon CTF 2018 - Chains of Trust (re391)
---

> Yet another reverse engineering challenge.
>
> P.S. It was tested on Ubuntu 17.10

As the binary connects to a server, follow the instructions [here](https://ctftime.org/task/6716) to set up the challenge locally. The intended solution is also attached by the challenge author there.

This was a really interesting challenge. Thank you so much [@gynvael](https://twitter.com/gynvael) for making this.

Before I start, small disclaimer: this is going to be a really long writeup. I will discuss more about the techniques I used to approach every part of this challenge, while attaching relevant pseudocode so that everyone can follow along, as well as talking about my thought process.

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
* **Main interface** - Prints the cool menu and reads the password
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
  memset(, 0, 0x1000);
  return res;
}
```

Troublesome... Self-decrypting code... I can either emulate this code using unicorn, or do what I did, which was just set a deeper breakpoint at where the decrypting was done, then dump the decrypted memory.

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

Or, maybe the flag is the concatenation of all `mysterious_byte`s. Again, using a short Python script, the `mysterious_byte` is always different, so unlikely to be the flag. (Gynvael is not so kind 😛)

Again, more thoughts came to mind, maybe it has something to do with the arithmetic being performed on the byte, etc. But enough speculation, more action. I should dump the subsequent pieces of code to find out.

### Automated Dumping
Clearly, we must automate the dumping process, since who knows how many more pieces of code there are. Also, if we do it by hand, we need to be super fast, or the connection to the server will timeout.

My first thought was to use the GDB script I wrote earlier for the CTF last week ([writeup](https://daniellimws.github.io/DCTF18-memsome.html)). To do this, I just need to find the `mmap`ed region in the **driver**, set a breakpoint at when the decryption is done, then dump the decrypted code. Simple.

However, there's a catch. It seems that Gynvael foresaw this coming. For every piece of code read from the server, there are random number of `nop` instructions in between, i.e. the address offset for when the decryption is done is not constant and the method mentioned above will fail.

I needed a way to calculate the offset before dumping. 😢

#### Scripting with GEF
Scripting GDB is not powerful enough. I want to directly access the memory and look for a specific instruction, so that I know where to set the breakpoint. 

I decided to leverage the Python API for GDB, and write a command to do this 😛. In particular, I am using GDB with GEF, so I am able to use the nice wrapper functions from GEF.

Now, what I am looking for is the first `mov rdx, rax` instruction (I've made sure there's no such instruction before this), and get the address of `call some_offset` which is the instruction before it.

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

I just classified this as useless code. Since my theory based on everything I found earlier was that this proof of work byte was useless. But still keep in mind that this exists since it could be related to the flag in the end.

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
The `0x17`th piece of code finally showed the sweet interface for me to enter the password.

The program `mmap`s a `RW` region, probably to store some information, and sends the address to the server.

After that, it does some fancy arithmetic to calculate the address of this code in the **driver**, as well as the number of bytes of code this program actually has. Then, it copies the code of this program to another `RWX` `mmap`ed region (since it is going to be cleared later for usage by the next retrieved code). Then, it spawns a thread running a function in the new `mmap`ed region. 😱 

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
char thread_main_menu(void* arg) {
    print_fancy_ui();
    read_n_bytes_from_stdin(32);

    *(arg + 9) = 1;

    while(true) {
        if (*(arg + 8))
            break;
        if (*(arg + 10)) {
            puts(*(arg + 0x4B));
        }

        mfence

        *(arg+10) = 0
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
Just now I said that was the only occurence of the sleeping code. I lied. After the validation thread, the server just sends some more code for the **driver** to sleep so that the program does not terminate. (Of course, if it takes too long the server will just give up and terminate the connection)

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
        if (*(arg + 8))
            break;
        
        for (int i = 0; i < 3; ++i) {
            char slot[8] = arg + 0x0A + i * 8;

            if (!slot[6]) {
                index = *((short*) slot[0]);
                *((short*) slot + 2) = buffer[index];
                mfence
                slot[5] = 1;
            }
            else {
                index = *((short*) slot[0]);
                buffer[index] = *((short*) slot + 2);
            }
            mfence
            slot[4] = 0;
            mfence
        }
    }
}
```

As seen here, the database has a storage space of 128 shorts. Other threads can either get or set values by modifying the `slot`. There are 4 `slot`s for each database, and the have the following structure.

```c
struct slot {
    short index,
    short value,
    bool done_set,
    bool done_get,
    bool is_set
}
```

### Processor
```
unpacked0x31.dump: --- Fresh code! ---
unpacked0x32.dump: --- Fresh code! ---
unpacked0x33.dump: --- Fresh code! ---
unpacked0x34.dump: --- Fresh code! ---
```

Following the database, I got 4 more threads that look identical.

```c
void processor_thread()
{
  arg = a1;
  for ( functions_table = *a1;
        !*((_BYTE *)arg + 8) && !(unsigned __int16)pull_value(32, functions_table, arg[2]);
        (*(void (**)(void))(functions_table + 80))() )
  {
    ;
  }
  for ( index = 0; index <= 7; index = index_2 + 1 )
  {
    seed = pull_value(index, functions_table, arg[2]);
    arg9 = *(unsigned __int8 *)(arga + 9);
    if ( arg9 == 1 )
    {
      seed += index_1 + 20384;
    }
    else if ( arg9 > 1 )
    {
      if ( arg9 == 2 )
      {
        seed ^= 0x73ABu;
      }
      else if ( arg9 == 3 )
      {
        seed += 9981;
      }
    }
    else if ( !*(_BYTE *)(arga + 9) )
    {
      seed *= 123;
    }
    push_value(index_1, seed, functions_tablea, *(_QWORD *)(arga + 16));
  }
  return push_value(33, 1, functions_table, arg[2]);
}
```

## Solution

threads
- find-thread
- telescope
- 6 types
- link them together (diagram)

solution
- doing everything reversed
- flag

[main_screenshot]:{{site.baseurl}}/ctfs/teaser-dragon-ctf-18/chains_of_trust/images/main.png
[packed_call_screenshot]:{{site.baseurl}}/ctfs/teaser-dragon-ctf-18/chains_of_trust/images/packed_call.png