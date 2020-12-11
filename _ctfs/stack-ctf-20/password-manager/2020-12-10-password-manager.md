---
layout: post
title: Password Manager (re)
ctf: STACK The Flags CTF 2020
permalink: /stack-ctf-20/password-manager
---

> Striking back! Your team has re-taken control over the gateway and recovered what seems to be a password manager used by COViD operatives. Unlock the database to retrieve the credentials.
>
> [CODEC.exe][codec]

First thing to do is always to check what type of program this is. Running `file` tells me that it is a .NET program.

```sh
➜ file CODEC.exe
CODEC.exe: PE32 executable (console) Intel 80386 Mono/.Net assembly, for MS Windows
```

Running the program in PowerShell gives the following output. Since it checks for a password, but does not read from standard input, I'm quite sure it reads the password from the program arguments.

```sh
PS S:\RE Challenges\re-challenge-3> .\CODEC.exe
Failed to verify master password
PS S:\RE Challenges\re-challenge-3> .\CODEC.exe aaaaa
Failed to verify master password
```

## Static Analysis

I used [dnSpy](https://github.com/dnSpy/dnSpy) to analyse the program. Make sure to use the win32 version of dnSpy because this is a PE32 executable.

Clicking on `<Module>` in the Assembly Explorer pane on the left will show the decompilation of the program.

![module][module]

In the explorer, we can also see `CrtImplementationDetails` and `CppImplementationDetails`, indicating that this program (or some parts of it) was compiled from C/C++ code.

The cleaned up version (with renamed symbols) of `main` is showed below. I added markers (`// [1]`, `// [2]`, etc) for easy reference to different sections of the code.

```cs
// Token: 0x06000003 RID: 3 RVA: 0x00001310 File Offset: 0x00000710
internal unsafe static int main(int argc, sbyte** argv)
{
    if (argc > 1)
    {
        // [1]
        sbyte* password = *(int*)(argv + 4 / sizeof(sbyte*));
        sbyte* password_start = password;
        sbyte* password_end = password;
        if (*password_start != 0)
        {
            do
            {
                password_end++;
            }
            while (*password_end != 0);
        }
        if (password_end - password_start == 32)
        {
            // [2]
            <Module>.g_INPUT = password;
            $ArrayType$$$BY0CB@D $ArrayType$$$BY0CB@D;
            <Module>.memmove((void*)(&$ArrayType$$$BY0CB@D), (void*)<Module>.g_INPUT, 32U);
            *(ref $ArrayType$$$BY0CB@D + 32) = 0;

            // [3]
            <Module>.printf("Decrypting database");
            byte[] hash = new byte[32];
            int count = 0;
            do
            {
                hash[num4] = <Module>.g_INPUT[num4];
                num4++;
            }
            while (count < 32);

            // [4]
            SHA256 sha = SHA256.Create();
            byte[] hash = sha.ComputeHash(array);
            uint count2 = 2000000U;
            do
            {
                hash = sha.ComputeHash(hash);
                count2 -= 1U;
            }
            while (count2 > 0U);

            // [5]
            if (array2[0] == 95 && array2[1] == 218)
            {
                // [6]
                <Module>.func1();
                <Module>.func4(<Module>.g_INPUT, 1);
                <Module>.func2();
                <Module>.func1();
                <Module>.func4(<Module>.g_INPUT, 13);
                <Module>.func2();

                // [7]
                bool correct = true;
                int num6 = <Module>.__imp_result + 3;
                byte* ptr = <Module>.g_INPUT + 1;
                byte* ptr2 = <Module>.__imp_result - <Module>.g_INPUT;
                uint count3 = 8U;
                do
                {
                    int num8 = (*(ptr - 1) == *(num6 - 3)) ? 1 : 0;
                    flag = (((flag ? 1 : 0) & (byte)num8) != 0);
                    int num9 = (*ptr == ptr2[ptr]) ? 1 : 0;
                    flag = (((flag ? 1 : 0) & (byte)num9) != 0);
                    int num10 = (ptr[1] == *(num6 - 1)) ? 1 : 0;
                    flag = (((flag ? 1 : 0) & (byte)num10) != 0);
                    int num11 = (ptr[2] == *num6) ? 1 : 0;
                    flag = (((flag ? 1 : 0) & (byte)num11) != 0);
                    num6 += 4;
                    ptr += 4;
                    count3 -= 1U;
                }
                while (count3 > 0U);

                // [8]
                if (correct)
                {
                    // print success message
                }
                else
                {
                    // print failed
                }
                return 0;
            }
            // print failed
            return 0;
        }
    }
    // print failed
    return 0;
}
```

The code is long, but could be summarized as follows:
* **[1]** Get the input from program arguments, and check if it is 32-bytes long.
* **[2]** Copy the input into another array data structure. Also saves the pointer to the input in `g_INPUT`.
* **[3]** Again copy the input into another array.
* **[4]** Compute the SHA256 of the input 2000000 times.
* **[5]** Compare the first 2 bytes of the hash, to determine whether to continue with the input validation.
* **[6]** Call `func1()`, `func(2)`, `func4()`, which probably does something with the input.
* **[7]** Compare `__imp_result` with `g_INPUT`.
  * The code in the do-while loop may seem complicated, but actually it just compares the bytes between the 2 arrays, like a `memcmp`.
  * Knowing that the code does this, we can speculate that our input (which `g_INPUT` points to) has been modified in **[6]**, then compared with `__imp_result` which is the target array of bytes obtained when the input is correct.
* **[8]** Prints the success or failure messages depending on the result of **[7]**.

So, the important parts of the program is **[6]**, where the input is most likely transformed, before it is checked in **[7]**.

**[4]** and **[5]** might look scary, as we need to make sure the first 2 bytes of the SHA256 hash of the input matches some values. However, it is actually not a big concern. It could be possible that there are many possible inputs that satisfy step **[7]**, and step **[5]** is just to narrow them down to only one case. We shall only worry about this after reversing step **[6]**.

#### `func1`

`func1` could be cleaned up as follows. I renamed the long symbol `<Module>.??_C@_0EB@IKAMFDMJ@?T?$JMz?d?$BA?aV?f?n?Y?$BOw?$LG?$HN?$IE?$DNmjD?$HL?FC?$BNa?$LJJ?$KI?$BJ90?O@` to `key`, and simplified the code in the loop:

```cs
// Token: 0x06000001 RID: 1 RVA: 0x0000117C File Offset: 0x0000057C
internal unsafe static void func1()
{
    int key_index = 32;
    sbyte* key_end = key;
    do
    {
        key_end++;
    }
    while (*key_end != 0);
    uint key_len = key_end - key;

    int input_index = 0;
    do
    {
        <Module>.g_INPUT[input_index + 0] += key[(key_index + 20) % key_len];
        <Module>.g_INPUT[input_index + 1] += key[(key_index + 30) % key_len];
        <Module>.g_INPUT[input_index + 2] += key[(key_index + 40) % key_len];
        <Module>.g_INPUT[input_index + 3] += key[(key_index + 50) % key_len];

        key_index = (key_index + 17) % key_len;
        input_index += 4;
    }
    while (input_index < 32);
}
```

In this function, each byte of the input is added with an offset, obtained from a global array `key`. We shall revisit this function later when writing the script to find the correct password.

#### `func2`

`func2` could be rewritten as the following.

```cs
// Token: 0x06000002 RID: 2 RVA: 0x00001234 File Offset: 0x00000634
internal unsafe static void func2()
{
    uint* ptr = (uint*)<Module>.g_INPUT;
    uint tmp;

    ptr[0] = ptr[0] >> 20 | ptr[0] << 12;

    tmp = ptr[0] ^ ptr[1];
    ptr[1] = tmp >> 20 | tmp << 12;

    tmp = ptr[1] ^ ptr[2];
    ptr[2] = tmp >> 20 | tmp << 12;

    tmp = ptr[2] ^ ptr[3];
    ptr[3] = tmp >> 20 | tmp << 12;

    tmp = ptr[3] ^ ptr[4];
    ptr[4] = tmp >> 20 | tmp << 12;

    tmp = ptr[4] ^ ptr[5];
    ptr[5] = tmp >> 20 | tmp << 12;

    tmp = ptr[5] ^ ptr[6];
    ptr[6] = tmp >> 20 | tmp << 12;

    ptr[7] =  ptr[6] ^ ptr[7];
}
```

This function takes the input as an array of `uint` (4-byte) values, i.e. consider 4 bytes as one block. Each block is xored with the one before it, then [rotated right](https://en.wikipedia.org/wiki/Circular_shift#Implementing_circular_shifts) by 12 bytes.

We shall revisit this function later when writing the script to find the password.

#### `func4`

If you tried to look for `func4` in the decompilation, you would realize it does not exist. Huh??? We could only find this:

```cs
// Token: 0x06000047 RID: 71 RVA: 0x00001090 File Offset: 0x00000490
[SuppressUnmanagedCodeSecurity]
[MethodImpl(MethodImplOptions.Unmanaged | MethodImplOptions.PreserveSig)]
internal unsafe static extern void func4(byte*, int);
```

Recall that earlier I mentioned that the program is likely compiled from `C/C++` code. So, the definiton of `func4` could be in native x86 assembly, so it does not appear in dnSpy. The next logical step is to find it, so I opened up the binary in Ghidra.

The question now is, where in the binary is the function? Notice that above the declaration of `func4`, there is the following signature.

```cs
Token: 0x06000047 RID: 71 RVA: 0x00001090 File Offset: 0x00000490
```

So, we do know the offset of the function in the binary. In particular `0x1090`, as given by `RVA: 0x00001090`. Navigating to `0x401090` in Ghidra (`0x400000` is the starting address assumed by Ghidra), I managed to obtain the decompilation of `func4`.

```c
uint func4(char *input, uint start)
{
    indices[32] = {0x1d, 0xd, 0x10, 0x14, /* and more */};
    counter = 0x10;

    do {
        index = start + 1 & 0x8000001f;
        if ((int)index < 0) {
            index = (index - 1 | 0xffffffe0) + 1;
        }

        c2 = (byte *)(input + indices[index]);
        index = start & 0x8000001f;
        if ((int)index < 0) {
            index = (index - 1 | 0xffffffe0) + 1;
        }

        c1 = (byte *)(input + indices[index]);
        start = start + 2;

        *c1 = *c1 ^ *c2;
        *c2 = *c2 ^ *c1;
        *c1 = *c1 ^ *c2;

        bVar1 = *c2 % 0x46 + *c1;
        *c1 = bVar1;
        *c2 = *c2 + bVar1 % 0x32;
        counter = counter + -1;
    } while (counter != 0);

    return bVar1 / 0x32;
}
```

*Tip: The following code is the [XOR swap algorithm](https://en.wikipedia.org/wiki/XOR_swap_algorithm).*

```c
*c1 = *c1 ^ *c2;
*c2 = *c2 ^ *c1;
*c1 = *c1 ^ *c2;
```

Here we see that the program
1. Takes 2 indices from the `indices` array
2. Swaps the values at those indices of the `input` array
3. Performs some operations (addition and modulus) on these values
4. Saves them back into the `input` array

#### `__imp_result`

Lastly, I need to know the values that the program is comparing the transformed input with, i.e. `__imp_result`. Similar to `func4`, the values of `__imp_result` cannot be found in the decompilation. Only the following declaration exists.

```cs
// Token: 0x04000037 RID: 55 RVA: 0x00004504 File Offset: 0x00002D04
internal unsafe static $ArrayType$$$BY0A@E* __imp_result;
```

However, when navigating to `0x4004504` (because `RVA: 0x4504`) in Ghidra, there seems to be some program metadata at this location, instead of a plain array of values to compare with.

```
                             IMAGE_LOAD_CONFIG_DIRECTORY32_00404460          XREF[1]:     004001c8(*)
        00404460               a4 00 00        IMAGE_LO                                                    = BB40E64Eh
                               00 00 00                                                                    = 00401edb
                               00 00 00                                                                    = 1Fh
        00404500               00              ??         00h
        00404501               00              ??         00h
        00404502               00              ??         00h
        00404503               00              ??         00h
        00404504               38              ??         38h    8                                         ?  ->  0040a038
        00404505               a0              ??         A0h
        00404506               40              ??         40h    @
        00404507               00              ??         00h
                             CLI_METADATA_HEADER
        00404508               42 53 4a        CLI_META                                                    must be 0x424a5342
                               42 01 00
                               01 00 00
                             CLI_Stream_#~
        00404574               00 00 00        #~                                                          Always 0
                               00 02 00
                               00 10 57
        004059e6               00              ??         00h
        004059e7               00              ??         00h

```

This makes sense, as `__imp_result` is an `$ArrayType$$$BY0A@E*` (whatever this is) object, and it probably contains the pointer to the actual array of values (same as `g_INPUT` as seen earlier). Nevermind, I can run the program in a debugger and look for the values in the program memory.

To do so, I set a breakpoint after a line that reads the value of `__imp_result`. I also need to set a breakpoint where the SHA256 hash is checked, so that I can modify the values to pass the check.

<video  style="display:block; width:100%; height:auto;" autoplay controls loop="loop">
    <source src="/ctfs/stack-ctf-20/password-manager/videos/imp_result.webm"  type="video/webm"  />
</video>

As shown in the video above, I was able to find the array in memory, by looking into the memory pointed by `num6`, which is assigned `__imp_result+3`.

### Time to find the password

Quick recap of the password checking routine:

```cpp
// [6]
<Module>.func1();
<Module>.func4(<Module>.g_INPUT, 1);
<Module>.func2();
<Module>.func1();
<Module>.func4(<Module>.g_INPUT, 13);
<Module>.func2();

// [7] (simplified)
memcmp(<Module>.g_INPUT, <Module>.__imp_result, 32);
```

Now that I briefly know what each of `func1`, `func2` and `func4` does, I can write a z3 script to find the password. I can reimplement the program in Python, then let the z3 solver solve for inputs that satisfy the checks.

First, I made some helper functions, to convert between blocks of 4 bytes and a single byte. This is to support the operations of `func2` as seen earlier.

```py
from z3 import *

# Combine 4 single bytes to a block of 4 bytes
def pack_bv(a):
    return Concat(a[3], a[2], a[1], a[0])

def pack_arr(arr):
    res = []
    for i in range(8):
        res.append(pack_bv(arr[i*4:i*4+4]))
    return res

# Split a block of 4 bytes into 4 single bytes
def unpack_bv(n):
    res = [0,0,0,0]
    res[3] = Extract(31, 24, n)
    res[2] = Extract(23, 16, n)
    res[1] = Extract(15, 8, n)
    res[0] = Extract(7, 0, n)
    return res

def unpack_arr(arr):
    res = []
    for i in range(8):
        res += unpack_bv(arr[i])
    return res
```

Then, I reimplemented `func1`, `func2` and `func4` in Python.

The steps I took to extract the offsets used in `func1` of the program are:
1. Set a breakpoint at the line after `func1` is called.
2. Provide an input of 32 `A`s.
3. Read the contents of `g_INPUT`, as each byte of the input is added with an offset value.
4. Subtract the bytes obtained in **Step 3** by 0x41 (`'A'`) to get the offsets.

```py
func_1_offsets = [166, 192, 238, 68, 225, 61, 74, 62, 29, 110, 6, 166, 23, 171, 20, 225, 124, 122, 182, 29, 217, 123, 48, 23, 168, 116, 4, 124, 210, 186, 165, 217]

def func1(arr):
    res = []
    for i in range(32):
        res.append(arr[i])

    for i in range(32):
        res[i] = res[i] + func_1_offsets[i]

    return res
```

```py
def func2(arr):
    arr = pack_arr(arr)

    res = []
    for i in range(8):
        res.append(arr[i])

    for i in range(7):
        b1_idx = i
        b1 = res[b1_idx]
        d1 = b1

        b2_idx = i + 1
        b2 = res[b2_idx]
        d2 = b2

        res[b2_idx] = RotateRight(d1, 20) ^ d2
        res[b1_idx] = RotateRight(d1, 20)

    res = unpack_arr(res)
    return res
```

```py
func_4_indices = [0x1d,0xd,0x10,0x14,4,0x16,0x15,0x18,0x1f,0xb,1,0,9,7,8,5,0x19,6,0x13,0xf,0x17,0x1b,3,2,0x1a,0x12,0x1e,0x1c,10,0xc,0x11,0xe]

def func4(arr, start):
    res = []
    for i in range(32):
        res.append(arr[i])

    for _ in range(16):
        i1 = func_4_indices[(start) % 32]
        i2 = func_4_indices[(start + 1) % 32]

        res[i1], res[i2] = res[i2], res[i1]
        tmp = URem(res[i2], 0x46) + res[i1]
        res[i1] = tmp
        res[i2] = res[i2] + URem(tmp, 0x32)

        start += 2
        start %= 32

    return res
```

With the functions defined, I replicate the part where the input is transformed.

```py
password_bvs = []
for i in range(32):
    password_bvs.append(BitVec("password_" + str(i), 8))

password = password_bvs

password = func1(password)
password = func4(password, 1)
password = func2(password)
password = func1(password)
password = func4(password, 13)
password = func2(password)
```

And set up the z3 `Solver` with constraints such that the transformed `password` matches the values in `imp_result` extracted earlier.

```py
solver = Solver()

imp_result = [0x76, 0xcf, 0x96, 0x48, 0x70, 0x61, 0x04, 0x8c, 0x1f, 0xc5, 0x25, 0xf3, 0xdc, 0xa0, 0x3c, 0xc8, 0x92, 0x8a, 0x2d, 0xeb, 0x24, 0x65, 0x8c, 0xf5, 0xd6, 0xb8, 0x11, 0x04, 0x6d, 0x90, 0x08, 0x60]
for i in range(32):
    solver.add(imp_result[i] == password[i])
```

Finally, ask the `solver` to solve for the password, and get flag.

```py
print(solver.check())
model = solver.model()

flag = []
for i in range(32):
    d = model[password_bvs[i]].as_long()
    flag.append(d)

print("".join("{:c}".format(s) for s in flag))
```

`govtech-csg{h0pp1ng_btwn_w0rlds}`

[codec]:{{site.baseurl}}/ctfs/stack-ctf-20/password-manager/CODEC.exe
[module]:{{site.baseurl}}/ctfs/stack-ctf-20/password-manager/images/module.png
[bp]:{{site.baseurl}}/ctfs/stack-ctf-20/password-manager/images/bp.png
[webm]:{{site.baseurl}}/ctfs/stack-ctf-20/password-manager/videos/imp_result.webm