---
layout: post
title: What is this weird program? (re)
ctf: STACK The Flags CTF 2020
permalink: /stack-ctf-20/weird-program
---

> We’ve intercepted this transmission between Oswell and COViD. It looks like a small program that allows them to communicate secretly with a key known only to them. Unfortunately the program that we have is lacking the key. It is likely that this program can be Tried Online with an Interpreter with a language that has been Extended.
>
> `⎕←{,⍉3↑(⎕D,⎕A)[1+16 16⊤¯0+'UTF-8'⎕UCS ⍵]} ⎕UCS⊥≠⌿⍤2⊤↑⎕UCS¨ ({⎕A[26|13+⎕A⍳⍵]}@(∊∘⎕A) '19T)8H+') ''`
>
> We have some ideas on how to find the key. It is known that Oswell has a bad memory, so it is likely that the key is available somewhere. It may also be possible to brute force the key instead.
>
> Note: Do put the flag into govtech-csg{} before submitting
>
> Addendum
> - You can use the organisation's website from "Who are the possible kidnappers". Some information from the organisation's website is useful in solving this challenge. There is no longer a need to complete that OSINT challenge to unlock this challenge.

Pasting the given code into Google search tells us that it is possibly the APL (Dyalog Extended) esoteric programming language. The code can be executed on [tio.run](https://tio.run/#apl-dyalog-extended) (Try It Online).

![tio][tio]

The syntax looks so weird, just like any programming language. It would be helpful to have some sense of how the syntax works. So I went to look at this [tutorial](https://tutorial.dyalog.com/next.html).

After 5 mins of looking at the tutorial, I decided that I do not want to reverse this at all.

My teammates [Lord_Idiot](https://lord.idiot.sg/) and [Alan](https://tcode2k16.github.io/blog) looked at this challenge before I did, and told me that they found the first part of the code (`{,⍉3↑(⎕D,⎕A)[1+16 16⊤¯0+'UTF-8'⎕UCS ⍵]}`) online, and realized that it hex-decodes the given argument.

With some quick searches on Google, I found these code snippets on [APLCart](https://aplcart.info/) and  [codegolf.stackexchange](https://codegolf.stackexchange.com/questions/207178/xor-two-strings).

![hex-decode][hex-decode]

![xor][xor]

![rot13][rot13]

This program basically does `hex_decode(xor(rot13('19T)8H+', <input>)))`. Looking at the challenge description again, I am supposed to find a key. The addendum also mentions that information from another OSINT challenge could be useful to solve this challenge.

I wasn't too sure what I was supposed to do, so I checked with the organizers, and clarified that `'19T)8H+'` is the ciphertext and I needed to find the key to decrypt it through the program. Since given in the challenge description that Oswell has a bad memory and it is likely that they key is available somewhere, I needed to find possible keys from the OSINT challenge that is related to Oswell. The organizer also clarified that the decrypted plaintext is human-readable text possibly in l33tsp34k.

So, my teammate [Creastery](https://www.creastery.com/) helped me dump all the 7-letter words from Oswell's corporate website, which forms the wordlist for the possible keys. I then wrote a simple Python script to try all the keys in the wordlist.

```py
from pwn import xor

msg = "19G)8U+"
with open("wordlist") as f:
    wl = f.read().rstrip().split("\n")

for i in wl:
    print(xor(i, msg))
```

Scrolling through the output, I found `AP1FL4G` which was the result of using `pivotal` as the key. Since this is readable, it is very likely that this should be the flag. And yup, submitting it to the challenge platform tells me challenge solved.

`govtech-csg{AP1FL4G}`


[tio]:{{site.baseurl}}/ctfs/stack-ctf-20/weird-program/images/tio.png
[xor]:{{site.baseurl}}/ctfs/stack-ctf-20/weird-program/images/xor.png
[rot13]:{{site.baseurl}}/ctfs/stack-ctf-20/weird-program/images/rot13.png
[hex-decode]:{{site.baseurl}}/ctfs/stack-ctf-20/weird-program/images/hex-decode.png