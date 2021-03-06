---
layout: post
title: exceptional (re)
ctf: DSO-NUS CTF 2021
permalink: /dso-nus-ctf-20/exceptional
---

> While sorting through some classified information, we found this binary from the depths of our archives. It came with a note that says this binary is EXCEPTIONal. Recover the unlock code and retrieve the content.
>
> [exceptional.exe][challenge]

I guess the challenge description hints that there is something to do with exceptions. Running the given program gives the following output.

![first-execution][first-execution]

Opening the program in the debugger shows the following:

![antidebug][antidebug]

Looks like I need to do some static analysis to find out what is happening.

### Static Analysis

Searching for references to the following string brings me to a function located at offset 0x1510.

```plaintext
GHIDRA and IDA are your best friends ^_^
```

The function is something like the following (simplified for readability):

```c
int func(int** param1)
{
    ...
    v1 = f1();

    if (v1 == 0)
    {
        v2 = f2()
        if (v2 == 0 && (...) < 1337)        // [1]
        {
            ...
            v3 = antidebug_messages;
        }
        else if (v2 == 0xc000001d)          // [2]
        {
            ...
            decrypt(...);
        }
        else if (v2 == 0xc0000094)          // [3]
        {
            v4 = f3(...);
            ...
            if (v4)                         // [6]
                read_unlock_code();
            else
                v3 = banter_messages;       // [5]
        }
        else if (v2 == 0xc0000096)          // [4]
        {
            ...
            // some code to perform byte by byte xor and comparisons
            if (unlock_code[i] ^ x == y)
                ...
            ...
        }
    }
    ...
    v4 = ... // choose a random string from the array assigned to v3
    printf("%s\n", v4);
}
```

The code above contains references to `antidebug_messages` and `banter_messages`. They are C string arrays as follows:

```plaintext
antidebug_messages:
00024e58    addr       s_Bad_Boi!           = "Bad Boi!"
00024e60    addr       s_Access_Denied!     = "Access Denied!"
00024e68    addr       s_Nope               = "Nope"
```

```plaintext
banter_messages:
00024e40    addr       s_GHIDRA_and_IDA_are_your_best_fri       = "GHIDRA and IDA are your best friends"
00024e48    addr       s_Start_with_static_analysis_:)_         = "Start with static analysis :)"
00024e50    addr       s_Try_harder!_                           = "Try harder!"
```

The code also calls the following functions (I won't explain them in detail, since they are relatively straightforward to understand when inspected in a decompiler.):

1. `read_unlock_code` - Prints `Enter Unlock Code:` and reads the unlock code from stdin, then stores it in a global variable.
2. `decrypt` - Decrypts a block of memory with Microsoft CryptoAPI functions, using the unlock code as the key. The program checks if the decrypted text starts with `tFWYaFjV`, and if true, prints out the full decrypted text.

  In other words, we know that the correct key will produce text that starts with `tFWYaFjV`.

**Observations:**

1. Some antidebugging efforts are present in the code (as seen in `[1]`).
2. The `if` statements all compare with a number starting with `0xc0` (as seen in `[2]`, `[3]` and `[4]`). If familiar with Windows, we would identify that these are exception numbers. For example:
    - `0xc0000094` - integer division by zero exception
    - `0xc0000096` - illegal memory access exception

   (Searching for references to this function, we can indeed verify that this function is registered as an exception handler for the program.)
3. Currently, the program seems to go down code path `[5]` to print some string (I call them banter messages) instead of requesting for the unlock code. It feels like we need to patch the conditional statement for the program to travel a different path.

With some more analysis, I confirmed that at program initialization, this function is registered as an exception handler. After all setup is done, the program intentionally exceutes instructions that will result in exceptions being triggered. The registered exception handler will check the exception number, and execute the corresponding code (as seen in `[2]`, `[3]`, `[4]`).

It should be fair to guess that the execution will follow the order:
`[3]` (read unlock code) --> `[4]` (does some xor operations and comparisons) --> `[2]` (decrypt block of memory with unlock code and print the result).

### Time for some patching

With the knowledge above, it is time to patch the program to execute in the way we want (i.e. ask for the unlock code). I modified the conditional statement at `[6]`, so that the program never goes the `else` path.

![enter-unlock-code][enter-unlock-code]

I also want to be able to inspect this program in a debugger. So in a similar way, I modified all conditional statements that would lead to the anti-debug messages being printed, making sure the program will never travel down those paths. That worked too. As seen below, now I can run the program in a debugger without the annoying anti-debug messages.

![antidebug-bypass][antidebug-bypass]

### Finding the key

Now's I'm left with the final, most important part - find out what is the key. In `[4]`, the `if (unlock_code[i] ^ x[i] == y[i])` is quite interesting. It is definitely validating the entered unlock code.

`y` seems to be a hardcoded global array. However, it is not that obvious what `x` is. So, I put a breakpoint at the xor instruction, to extract the values in `x` for each `i`.

With that, a simple `"".join([x[i] ^ y[i] for i in range(len(x))])` (in Python) gives the correct unlock code: `Y0u_4r3_th3_M@5t3r_0f_Exc3pt10n5`.

#### Doesn't work?

I entered the unlock code into the program, but there was no output. I set some breakpoints in the debugger, and realized the following line in `decrypt` gave the error.

```c
CryptAcquireContextW(&hCryptContext,(LPCWSTR)0x0,L"Microsoft Enhanced Cryptographic Provider v1.0",1,0);
```

Looking at the `LastError` in the debugger tells me that my Windows version (Windows 7) does not support the provider above. I forgot to prepare a Windows 10 VM for the competition 😬. So I got my teammate [@Lord_Idiot](https://blog.idiot.sg) to help me run it in his Windows 10 VM, and we get a very long base64 text as output.

After decoding it a few times, we get the flag.

`DSO-NUS{30af389712e14b130e932772e0a1e1f06b8d033a410de17e691718c2d29144d5}`


[challenge]:{{site.baseurl}}/ctfs/dso-nus-21/exceptional/ctf.exe
[antidebug]:{{site.baseurl}}/ctfs/dso-nus-21/exceptional/antidebug.png
[first-execution]:{{site.baseurl}}/ctfs/dso-nus-21/exceptional/first-execution.png
[enter-unlock-code]:{{site.baseurl}}/ctfs/dso-nus-21/exceptional/enter-unlock-code.png
[antidebug-bypass]:{{site.baseurl}}/ctfs/dso-nus-21/exceptional/antidebug-bypass.png