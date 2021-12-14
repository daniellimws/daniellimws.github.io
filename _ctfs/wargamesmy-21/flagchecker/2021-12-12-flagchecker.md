---
layout: post
title: flagchecker (re)
ctf: Wargames.MY 2021
permalink: /wargamesmy-21/flagchecker
---

[Challenge file][Challenge]

```sh
$ ./chal
Enter flag: wgmy
Wrong flag..
```

### Static Analysis

After loading the binary in Ghidra, this is what we get (code cleaned up for better readability):

```c
int main() {
    ...

    printf("Enter flag: ");
    __isoc99_scanf("%39s",input);
    i = 0;

    while( true ) {
        len = strlen(input);
        if (len <= i) break;

        for (j = 0; j < 8; j = j + 1) {
            uVar1 = input[i] >> (j & 0x1f) & 1;
            iVar4 = FUN_00101207(i + 1);
            uVar2 = iVar4 >> (j & 0x1f) & 1;
            uVar3 = FUN_001011e9(uVar1, uVar2);
            uVar1 = FUN_001011e9(uVar3, uVar1);
            uVar2 = FUN_001011e9(uVar3, uVar2);
            uVar1 = FUN_001011e9(uVar2, uVar1);
            iVar4 = FUN_001011e9(uVar1, uVar1);
            mutated[i] = mutated[i] | (iVar4 << (j & 0x1f));
        }

        i = i + 1;
    }

    res = strcmp(HARDCODED, mutated);
    if (res == 0) {
        puts("Correct flag!");
    }
    else {
        puts("Wrong flag..");
    }
    ...
}
```

This `main` function is not too big, and can be split into 3 parts:

1. Reading input with `scanf`
2. Doing something to the input and saving the changes somewhere else
3. Comparing the modified input with another string

The most important part is definitely part 2

```c
    while( true ) {
        len = strlen(input);
        if (len <= i) break;

        for (j = 0; j < 8; j = j + 1) {
            // [1]
            uVar1 = input[i] >> (j & 0x1f) & 1;

            // [2]
            iVar4 = FUN_00101207(i + 1);
            uVar2 = iVar4 >> (j & 0x1f) & 1;
            uVar3 = FUN_001011e9(uVar1, uVar2);
            uVar1 = FUN_001011e9(uVar3, uVar1);
            uVar2 = FUN_001011e9(uVar3, uVar2);
            uVar1 = FUN_001011e9(uVar2, uVar1);
            iVar4 = FUN_001011e9(uVar1, uVar1);

            // [3]
            mutated[i] = mutated[i] | (iVar4 << (j & 0x1f));
        }

        i = i + 1;
    }
```

It loops through each byte in the input, and has a nested loop that:

* goes through each bit in the current byte
  * `input[i] >> (j & 0x1f) & 1`  ---- `// [1]`
* modifies the bit
  * whole series of function calls and assignments ---- `// [2]`
* and saves it into a buffer,
  * `mutated[i] = `
* at the same byte position,
  * `mutated[i] = mutated[i] ...`
* and at the same bit position
  * `mutated[i] = mutated[i] | (iVar4 << (j & 0x1f))` ---- `// [3]`

Now, to see what happens inside the 2 functions `FUN_00101207` and `FUN_001011e9` that are called:

```c
int FUN_00101207(int param_1)
{
    int local_18;
    int local_14;
    int local_10;
    int i;

    local_18 = 0;
    local_14 = 2;
    while( true ) {
        local_10 = 0;
        for (i = 1; i <= local_14; i = i + 1) {
            if (local_14 % i == 0) {
                local_10 = local_10 + 1;
            }
        }
        if ((local_10 == 2) && (local_18 = local_18 + 1, local_18 == param_1)) break;
        local_14 = local_14 + 1;
    }

    return local_14;
}
```

On first glance, this function seems to take a number as an argument, and return another number. I'm not in a hurry to know what exactly happens to the argument, so I just keep this in mind.

Next one:

```c
bool FUN_001011e9(uint a, uint b)
{
  return (a | b) == 0;
}
```

This one is easier to understand, just returning whether both of them are 0, i.e. `!(a | b)` or `!a & !b`.

In the end, the thing to focus on is these 5 lines of code:

```c
    iVar4 = FUN_00101207(i + 1);
    uVar2 = iVar4 >> (j & 0x1f) & 1;
    uVar3 = FUN_001011e9(uVar1, uVar2);
    uVar1 = FUN_001011e9(uVar3, uVar1);
    uVar2 = FUN_001011e9(uVar3, uVar2);
    uVar1 = FUN_001011e9(uVar2, uVar1);
    iVar4 = FUN_001011e9(uVar1, uVar1);
    mutated[i] = mutated[i] | (iVar4 << (j & 0x1f));
```

But I didn't really want to reverse this also. I decided to write a script to find the flag for me. I decided to modify the script I wrote for a [challenge I solved](/inctf-20/jazz) some time ago.

Here are the things I know that happens to my input:

* Each byte goes through a set of operations
* Each byte's changes do not rely on the bytes next to it (99% sure)
* The final result is compared with a hard-coded string (`strcmp(HARDCODED, mutated)`)

And this is the plan (in pseudocode):

```py
flag = ""
for i in range(39):     # because it expects 39 chars from the scanf
    for c in "abcdef" + string.digits + "{}_!@":        # the flag charset
        run program with input = flag + c
        breakpoint at right before strcmp   # because at this point, all chars in input are modified

        if mutated[i] == hardcoded[i]:      # good, we know the flag's char at this position
            flag += c                       # save it
            break                           # now break to try the next position

        else:                               # wrong, we don't know the flag's char at this position yet
            continue                        # try next option in the charset
```

This is scriptable in GDB. First I make a script that sets a breakpoint right before the `strcmp` call. This script is in GDB scripting syntax.

```sh
# silentbreak
break *0x555555554000+0x142d
commands
silent          # this is to make GDB keep quiet when it reaches this breakpoint
end
```

Then, here's a script written in Python to execute the plan laid out above.

```py
import string

cs = "abcdef" + string.digits + "{}_!@"     # the flag charset
flag = "wgmy"                               # i know the flag starts with this

gdb.execute("gef config context.enable 0")  # to disable the context panel output

for i in range(4, 39):                      # 39 chars expected by scanf
    for c in cs:                            # trying each char in the charset

        # this is one way to supply input to a program running in GDB
        open("in", "w").write(flag + c)
        gdb.execute(f"run < in")

        # read_memory and get_register are GEF functions
        # so GEF must be installed to use them
        # rdi is the hardcoded string
        # rsi is the mutated input
        # read the byte at current offset from each string
        mutated = read_memory(get_register("$rsi") + i, 1)
        hardcoded = read_memory(get_register("$rdi") + i, 1)

        # if correct, yay
        if mutated == hardcoded:
            flag += c
            print(flag)
            open("flag.txt", "w").write(flag)
            break       # move on to next byte index
```

Finally, run the scripts in GDB batch mode:

<script id="asciicast-58XKCBPpDPiOBq7ZTM4llWghX" src="https://asciinema.org/a/58XKCBPpDPiOBq7ZTM4llWghX.js" async></script>

[challenge]:{{site.baseurl}}/ctfs/wargamesmy-21/flagchecker/chal