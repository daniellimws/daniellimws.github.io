---
layout: post
title: memsome (re110)
ctf: DefCamp CTF Quals 2018
---

> I can not find my license file. Can you help me? 
>
> Target: [file](https://raw.githubusercontent.com/daniellimws/daniellimws.github.io/master/_posts/dctf-quals-18/memsome/memsom)
>
> Author: Lucian Nitescu

```console
 $ file memsom                             
memsom: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=2acc3f22c1576a93
402ac5c4f3d1f0ef88ca3db5, stripped

 $ ./memsom                                    
Welcome! Scanning for license file!                                                              
Piracy is bad!
```

We are given a 64-bit stripped, dynamically-linked ELF binary, that seems to be doing something with a license file.

## Static Analysis
Opening this up in IDA, seeing strings like 
```cpp
std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string(char const*,std::allocator<char> const&)
```

immediately tells us that this is a C++ binary.

Hex-Rays pseudocode for C++ is not the best, but way way better than looking at the disassembly graph, so just hit F5.

### C++
(For people unfamiliar with C++ reversing) 

Before diving into the pseudocode, there are some things to know that will help in understanding the code better. [Skip to next section](#pseudocode).

#### this
As C++ is an object-oriented language, it is important to know how each object call their member functions in low level terms.

In C++, all objects have access to their member variables and functions through the `this` keyword. How this is able to work in low level is by passing in the object as the first argument of every function. This is similar to how all class functions in python have `self` as their first argument.

For example, 

```cpp
len = std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::length(str);
```

is equivalent to

```cpp
len = str.length();
```

#### Operators
In addition, most, if not all operators are also functions by themselves, such as `operator=` or `operator+`.

For example,

```cpp
std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator=(&input_line_rot13, tmp_str);
```

is equivalent to

```cpp
input_line_rot13 = tmp_str;
```

#### Destructors
As there are constructors, there are also destructors in C++ that are in charge of cleaning up. They look like a constructor, but with a `~` in front. For example, if `Dog` is the class name, `~Dog()` is the destructor.

Since their purpose is just to clean up, we can ignore all destructors in the code.

#### String
As `std::string` is just a typedef for `std::basic_string<char>`, it always shows up as `std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::` instead of `std::string` or something shorter.

Refer to [https://en.cppreference.com/w/cpp/string/basic_string](https://en.cppreference.com/w/cpp/string/basic_string) for more info.

<br/>

Knowing all these, the pseudocode would not look as scary as you would think it does.

### Pseudocode
Faced with 581 lines of code, this sure is daunting. However, a quick skim through the code, we can identify a few main parts. We shall look at them one by one.

*The binary is stripped so all symbols below (non c++ standard library functions) were renamed by me, and the user-defined functions are all in the form `func(dest, src)` just like `strcpy`.*

#### Anti-debug
The first part is a series of `if` statements that looks to be doing some anti-debugging measures.

```cpp
start_time = times(0LL);
if ( ptrace(0, 0LL, 1LL, 0LL) < 0 )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)print_scan_license_file + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)rot13 + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)try_harder + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)main + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)b64decode + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)b64encode + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)is_traced + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)hex_encode + 1) == 0xCC )
    try_harder(0LL);
if ( (unsigned __int8)*((_DWORD *)hex_decode + 1) == 0xCC )
    try_harder(0LL);
```

First one is a standard `ptrace` anti-debugging check [^1] and the rest checks if breakpoints [^2] are set at the start of a few functions.

Dealing with this is quite straightforward. Just patch [^3] the binary by replacing the `ptrace` call with `nop` instructions. As for the breakpoint checks, I just ignored them as I could just attach a breakpoint **not** at the first instruction of the function.

Also, do notice that the program stores the time at the start.

[^1]: The general idea is that debuggers, such as **gdb**, utilize the `ptrace()` function to attach to a process at runtime. Because only one process is allowed to do this at a time, if `ptrace` returns -1, it means attaching failed and there has already been another process that has attached to this binary. [https://www.aldeid.com/wiki/Ptrace-anti-debugging](https://www.aldeid.com/wiki/Ptrace-anti-debugging)

[^2]: Debuggers like **gdb** attach breakpoints by temporarily modifying the instruction at a given address to `0xCC` (int 3 instruction), which will trigger `SIGTRAP` when executed and hands over control to the debugger. [https://0x00sec.org/t/re-guide-for-beginners-bypassing-sigtrap/2648](https://0x00sec.org/t/re-guide-for-beginners-bypassing-sigtrap/2648)

[^3]: <p>Demonstration on patching using IDA</p><iframe width="560" height="315" src="https://www.youtube.com/embed/g5UJi_zen18?rel=0&amp;controls=0&amp;showinfo=0&mute=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

#### Program input
While running the binary earlier, there was no prompt for any user input. However, one of the printed lines contains `Scanning for license file!`. Indeed, the program looks for the input provided in the file `.secret-license-file`.

```cpp
std::basic_ifstream<char,std::char_traits<char>>::basic_ifstream(&secret_file_ifs, "./.secret-license-file", 8LL);
if ( (unsigned __int8)std::basic_ifstream<char,std::char_traits<char>>::is_open(&secret_file_ifs) )
{
    // ----- rot13 the first line -----
    std::getline<char,std::char_traits<char>,std::allocator<char>>(&secret_file_ifs, &input_line);
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string(
        &input_str,
        &input_line);
    rot13((__int64)tmp_str, (__int64)&input_str);
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator=(&input_line_rot13, tmp_str);

    // destructors. not important.
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)tmp_str);
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&input_str);

    // probably also to make sure no debugging is happening
    if ( (unsigned int)times(0LL) != (_DWORD)start_time )
        try_harder(0LL);
```

As we can see here, the program opens an `ifstream` to the file `.secret-license-file`, checks if it is open, then reads a line from it. After that, the input is `rot13` "encoded" and stored in `input_line_rot13`.

Subsequently, it seems like the program also checks if the current time is equal to the starting time. But it does not seem to affect me so just ignore it.

#### Preparing array of strings
This is the part that makes the program look so long. Although there are almost 600 lines of code, around 350 is from just repeating this segment of code.

```cpp
    // unknown_str = unknown1; (unknown1 is hardcoded string in memory)
    std::allocator<char>::allocator(&allocator);
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string(
        &unknown_str,
        &unknown1,
        &allocator);
    hex_encode((__int64)hash_array[0], (__int64)&unknown_str);

    // destructors. not important
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&unknown_str);
    std::allocator<char>::~allocator(&allocator, &unknown_str);

    // unknown_str = unknown2; (unknown2 is hardcoded string in memory)
    std::allocator<char>::allocator(&allocator);
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string(
        &unknown_str,
        &unknown2,
        &allocator);
    hex_encode((__int64)&hash_array[32], (__int64)&unknown_str);

    // destructors. not important.
    std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&unknown_str);
    std::allocator<char>::~allocator(&allocator, &unknown_str);
```

In essence, the program copies some hard-coded string, hex-encodes it, and stores it in an array, one by one, for a total of 70 strings.

(The array is named `hash_array` as we would find out later that it is a whole list of hashes.)

#### Comparing hashes
This is the last chunk of code in the `main` function. Long but contains a lot of destructors that we can ignore.

```cpp
    pass_or_not = 1;

    // not sure what this does but locale probably means not important
    // my assumption was right since skipping this I still got the flag
    for ( i = 0; i <= 69; ++i )
    {
        std::locale::locale((std::locale *)&allocator);
        sub_5A1F((__int64)&tmp_str[32 * i], (__int64)&allocator);
        std::locale::~locale((std::locale *)&allocator);
    }

    // comparing hashes with hardcoded strings
    for ( j = 0; j <= 69; ++j )
    {
        std::allocator<char>::allocator(&allocator);

        // c = input_line_rot13[j]
        c = (char *)std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator[](&input_line_rot13, j);

        // rot13_j = string(c)
        std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string(&rot13_j, 1LL, (unsigned int)*c, &allocator);
        
        b64encode((__int64)&b64_rot13_j, (__int64)&rot13_j);
        md5((__int64)&tmp, (__int64)&b64_rot13_j);
        md5((__int64)&calculated_hash, (__int64)&tmp);
        secret_str = &tmp_str[32 * j];

        strings_are_same = (unsigned __int8)are_strings_equal((__int64)&calculated_hash, (__int64)secret_str) && pass_or_not == 1;
        
        // destructors. not important.
        std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&calculated_hash);
        std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&v26);
        std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&b64_rot13_j);
        std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&rot13_j);
        std::allocator<char>::~allocator(&allocator, secret_str);

        // also lots of destructors and pointless stuff. not important.
        if ( strings_are_same )
        {
            for ( k = 0; k <= 1199; ++k )
            {
                std::allocator<char>::allocator(&allocator);
                v6 = (char *)std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator[](&input_line_rot13, k);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::basic_string(&v20, 1LL, (unsigned int)*v6, &allocator);
                b64encode((__int64)&v21, (__int64)&v20);
                md5((__int64)&v22, (__int64)&v21);
                md5((__int64)&v23, (__int64)&v22);
                md5((__int64)&rot13_j, (__int64)&v23);
                md5((__int64)&b64_rot13_j, (__int64)&rot13_j);
                md5((__int64)&v26, (__int64)&b64_rot13_j);
                md5((__int64)&calculated_hash, (__int64)&v26);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator=(&v19, &calculated_hash);

                // Destructors. Doesn't matter.
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&calculated_hash);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&v26);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&b64_rot13_j);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&rot13_j);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&v23);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&v22);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&v21);
                std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string((__int64)&v20);
                std::allocator<char>::~allocator(&allocator, &calculated_hash);
            }
        }
        // if the strings are not the same then we fail
        else
        {
            pass_or_not = 0;
        }
    }
    if ( pass_or_not == 1 )
        // cout << "You have installed your software";
        v7 = std::operator<<<std::char_traits<char>>(&std::cout, "You have installed your software!");
    else
        // cout << "Piracy is bad!";
        v7 = std::operator<<<std::char_traits<char>>(&std::cout, "Piracy is bad!");
```

The first for loop seems to be something about locales so I assumed that it was not important. Later my assumption was confirmed as there was no difficulty getting the flag despite skipping this part.

Here, the important part is the second for loop, in which the user input is being compared with the hardcoded strings prepared earlier. In particular, the following pseudocode should sum up what is being done.

```python
is_correct = True
for i in range(70):
    if md5(md5(b64encode(input_line_rot13[i]))) != hash_array[i]:
        is_correct = False

if is_correct:
    print("You have installed your software!")
else:
    print("Piracy is bad!")
```

This is it. To sum up everything, we just need to provide a 70-byte string that satisfies `md5(md5(b64encode(input_line_rot13[i]))) == hash_array[i]`.

Before going on to solving this, I would like to discuss the `md5` function here, which was stripped, hence it was not given that this function performs a `md5` hash. As you can see the code isn't very complicated, but the number of solves is relatively low (67 solves), so this may be the reason.

You could skip to the [solution](#solution) if you are not interested in the following section.

##### `md5`
In IDA, this was originally labelled as `sub_766C`, and the function definition is as follows.

```cpp
__int64 __fastcall sub_766C(__int64 str1, __int64 str2)
{
  char v3; // [rsp+10h] [rbp-88h]
  unsigned __int64 canary; // [rsp+88h] [rbp-10h]

  canary = __readfsqword(0x28u);
  sub_61D4((__int64)&v3, str2);
  sub_749C(str1, &v3);
  return str1;
}
```

In the 2 functions being called here, there are also calls to other functions, which goes on and on. I had to admit, I went down the rabbit hole of trying to reverse every single function I encountered, but still could not see anything. Unlike the one with the locale, I believed this should not be skipped since there's no assumption that could be made about it.

Soon, it striked to me that it could be a hash function or some encryption method, since there was no standard library functions being referenced down the call chain, and programmer-written code would not be this complicated unless it is either hashing or encryption.

I stumbled upon a function which allowed me to suspect that this is a `md5` hash function, due to the presence of the magic numbers [^4].

[^4]: Each hash function has a set of "magic numbers", which are constants applied to the argument that is to be hashed. For `md5` in particular, they are `0x67452301`, `0xefcdab89`, `0x98badcfe` and `0x10325476`. They are shown in variables `a0`, `b0`, `c0` and `d0` in the [md5 pseudocode](https://en.wikipedia.org/wiki/MD5#Pseudocode).

```cpp
__int64 __fastcall sub_6232(__int64 a1)
{
  __int64 result; // rax

  *(_BYTE *)a1 = 0;
  *(_DWORD *)(a1 + 68) = 0;
  *(_DWORD *)(a1 + 72) = 0;
  *(_DWORD *)(a1 + 76) = 0x67452301;
  *(_DWORD *)(a1 + 80) = 0xEFCDAB89;
  *(_DWORD *)(a1 + 84) = 0x98BADCFE;
  result = a1;
  *(_DWORD *)(a1 + 88) = 0x10325476;
  return result;
}
```

This was just a very educated guess but there is no guarantee. To be safe, I should have set a breakpoint at this function (`sub_766C`) and observed the result to confirm my suspicion. However, me being lazy just decided to implement the solution and worry later.

## Solution
There are 2 parts to solving this,
1. Extracting all the 70 hashes that need to be matched
2. Brute force the character that matches

### Extracting hashes
I decided to achieve this by dumping the memory using gdb. With gef, I could set a breakpoint despite PIE enabled.

```bash
gef➤  pie break *0x4778
gef➤  pie run
```

Then, I inspected the memory of `hash_array`.

```bash
gef➤  telescope $rsp+0x390
0x00007fffffffdae0│+0x00: 0x0000555555773310  →  "98678DE32E5204A119A3196865CC7B83"      ← $r12
0x00007fffffffdae8│+0x08: 0x0000000000000020
0x00007fffffffdaf0│+0x10: 0x0000000000000020
0x00007fffffffdaf8│+0x18: 0x00000000003080f8
0x00007fffffffdb00│+0x20: 0x0000555555773440  →  "E5A4DC5DD828D93482E61926ED59B4EF"
0x00007fffffffdb08│+0x28: 0x0000000000000020
0x00007fffffffdb10│+0x30: 0x0000000000000020
0x00007fffffffdb18│+0x38: 0x0000000000307d70 ("p}0"?)
0x00007fffffffdb20│+0x40: 0x0000555555773470  →  "68E8416FE8D00CCA1950830C707F1E22"
0x00007fffffffdb28│+0x48: 0x0000000000000020
```

Since this is an array of `string` objects, each element's first 8 bytes points to the location of the array of characters in the heap. This makes extracting the strings troublesome since I could not just dump a contiguous chunk of memory.

So, I decided to write a gdbscript to do this.

```
pie break *0x4778
pie run

set $i = 0

while ($i < 70)
    set $start = *((long long*)($rsp+0x390+$i*32))
    set $end = *((long long*)($rsp+0x390+$i*32))+32
    append memory hashes.bin $start $end
    set $i++
    end

p "[+] Done extracting hashes..."
```

```bash
gef➤  help append memory
Append contents of memory to a raw binary file.
Arguments are FILE START STOP.  Writes the contents of memory within the
range [START .. STOP) to the specified FILE in raw target ordered bytes.
```

```bash
gef➤  source gdbscript
```

### Brute force characters
Now that we have the hashes, finding the flag is quite straightforward.

```py
import hashlib
import string

def read_hashes(f):
    hashes = open(f, "r").read()
    hashes = [hashes[i*32:(i+1)*32].decode("hex") for i in range(70)]
    return hashes

def rot13(s):
    tr = string.maketrans( 
        "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz", 
        "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm")
    return string.translate(s, tr)

def solve(target):
    for c in string.printable:
        b64 = c.encode("base64")[:-1]
        m = hashlib.md5(b64).hexdigest()
        m = hashlib.md5(m).hexdigest()
        m = m.decode("hex")
        if target == m:
            return c
    
    raise Exception("gg cannot find")

hashes = read_hashes("hashes.bin")
flag = ""
for h in hashes:
    flag += rot13(solve(h))

print flag
```

The flag is `DCTF{9aa149d1a8a825f582fa7684713ca64ec77ff33bda71de76b51b0a8f1026303c}`.

All resources can be downloaded [here](https://github.com/daniellimws/daniellimws.github.io/tree/master/_posts/dctf-quals-18/memsome).

***