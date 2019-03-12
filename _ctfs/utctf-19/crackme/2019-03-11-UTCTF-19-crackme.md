---
layout: post
title: crackme (re1200)
ctf: UTCTF 2019
---

> Attention all UTCTF players, asper is in great danger, and he needs YOUR help to reverse engineer this [binary][crackme] and figure out the password. To do this, he needs IDA Pro and a couple of breakpoints. To help him, all he needs is your credit card number, the three numbers on the back, and the expiration month and date. But you gotta be quick so that asper can secure the flag, and achieve the epic victory R O Y A L.
>
> Note: the flag is the password with utflag{} wrapped around it.
> 
> by jitterbug_gang
>
> Also, this binary was compiled a little differently, and you may need to install some extra dependencies to run it. (Or you can try solving this with just static analysis.) Try installing libc++abi-dev and libcxxtools-dev to run this challenge.
> 
> If that doesn't work for you, try to preload this libc file with LD_PRELOAD.

```c
int main(void) {
  int correct;
  size_t len;
  double dVar1;
  int counter;
  int index;
  char input[0x40];
  
  setbuf(stdin, 0);
  setbuf(stdout, 0);
  printf("Please enter the correct password.\n>");
  fgets(input, 0x40, stdin);

  len = strlen(input);

  try {
    dVar1 = divide(0x20,0);
  }
  catch {
    // ghidra doesn't decompile this part properly
  }

  index = 0;
  while (index < len) {
    input[index] = input[index] ^ 0x27;
    index = index + 1;
  }

  counter = 0;
  while (counter < 0xcb) {
    stuff[counter] = stuff[counter] - 1 ^ stuff2[(0xca - counter)];
    counter = counter + 1;
  }

  (*(code *)stuff)(input,len);

  correct = memcmp(test,input,0x40);
  if (correct == 0) {
    printf("Correct Password!");
  }
  else {
    printf("Incorrect password.\n");
    printf(
          "utflag{wrong_password_btw_this_is_not_the_flag_and_if_you_submit_this_i_will_judge_you}\n"
          );
  }
  return 0;
}
```

After opening the given binary in GHIDRA, we can obtain the pseudocode above in `main`. It looks rather straightforward, with the program doing the following

1. Read 0x40 bytes of input
2. Calculates 0x20/0 ???
3. Xors all input bytes with 0x27
4. Does some xor computations with bytes in `stuff`
5. Calls `stuff` as a function with our input and length as arguments
6. Checks if our input matches `test`

### Extracting the encryption function
From this, we can speculate that `stuff` does something to our input, before `memcmp` is used to check it. So, the obvious plan is to extract `stuff` after it is manipulated, and reverse whatever is being done in it.

We can achieve that by setting a breakpoint right before `memcmp` is called, since at that point `stuff` would have contained the correct opcodes. Let's do that in GDB. But hmm, nothing happens when I run the binary, and the process just exited.

```
gef➤  break *0x400d8c
Breakpoint 1 at 0x400d8c
gef➤  r
Starting program: /root/ctfs/utctf19/crackme/crackme
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".
[Inferior 1 (process 1745) exited with code 01]
```

There could have been some anti-debug measures in place. When trying to search for references to `ptrace()` in the binary, I found this in `csu_init()`.

*`csu_init` is called before `main`*

```c
void _csu_init(void)
{
  long ret;
  
  ret = ptrace(PTRACE_TRACEME, 0, 1, 0);
  if (ret == -1) {
    exit(1);
  }
}
```

This is a standard way to prevent GDB to attach to the process and debug it, since every process is only allowed to have one tracer.

No big deal, we can just patch the `call` instruction to a `nop` instead. (There is currently an issue with GHIDRA when trying to patch binaries after auto-detecting its format. Check this [issue](https://github.com/NationalSecurityAgency/ghidra/issues/19).)

Now with our patched binary, we can attach GDB to break before `memcmp` is called and dump the contents of `stuff`. From the loop in the pseudocode above, we know that `stuff` contains 0xcb bytes. Dumping memory in GDB is very simple.

```
gef➤ dump memory stuff 0x602090 0x60215b
```

After that, we can open `stuff` in GHIDRA.

![stuff][stuff]

So many instructions... How about looking at the pseudocode.

```c
void stuff(char* input, ulong len) {
  int index = 0;
  while (index < len) {
    input[index] = in[index] ^ (index + 0x33);
    index++;
  }
}
```

Way better.

### Reversing it

The next logical step is to apply the reverse of this function to `test`, which is compared with our input after being modified by this function. I wrote a simple C program that would take in `test` as input and print out after decrypting it.

```c
#include <stdio.h>

int main() {
    char flag[0x41];
    fgets(flag, 0x40, stdin);

    for (int i = 0; i < 0x40; ++i) {
        flag[i] = flag[i] ^ (0x33 + i);
        flag[i] ^= 0x27;
    }

    flag[0x39] = 0;

    puts(flag);
}
```

With this in place, we need to also dump the contents of `test` so that we can decrypt it.

```
gef➤ dump memory test 0x602230 0x602270
```

Then,

```
~/ctfs/utctf19/crackme ➤ gcc solve.c
~/ctfs/utctf19/crackme ➤ cat flag | ./a.out
1_hav3_1nf0rmat10n_that_w1ll_lead_t0_th3_arr3stf_cspp3rstick6
```

Before submitting the flag, I entered it into the given binary for a sanity check. But it tells me this is wrong?

Recall the `divide(0x20, 0)` enclosed in a `try/catch` block. Apparently in the `catch` block there are some manipulations being done to our input as well, which GHIDRA did not show in the pseudocode.

```c
try {
  dVar1 = divide(0x20,0);
}
catch {
  // ghidra doesn't decompile this part properly
}
```

Since dividing anything by 0 would cause an exception, the code inside the `catch` block will be executed.
Perhaps this was a way to hide the code.
But anyways, it wasn't very complicated, just 2 additional lines.

```c
try {
  dVar1 = divide(0x20,0);
}
catch {
  // ghidra doesn't decompile this part properly
  input[47] ^= 0x44;
  input[52] ^= 0x43;
}
```

Adding this to our decryption code, we get the correct flag.

```
~/ctfs/utctf19/crackme ➤ cat flag | ./a.out
1_hav3_1nf0rmat10n_that_w1ll_lead_t0_th3_arr3st_0f_c0pp3rstick6
```

[crackme]:{{site.baseurl}}/ctfs/utctf-19/crackme/crackme
[stuff]:{{site.baseurl}}/ctfs/utctf-19/crackme/images/disas.png

---