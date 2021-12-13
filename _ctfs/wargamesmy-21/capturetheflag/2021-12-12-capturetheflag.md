---
layout: post
title: capturetheflag (re)
ctf: Wargames.MY 2021
permalink: /wargamesmy-21/capturetheflag
---

We were given a [sb3][challenge] file for this challenge. A quick online search shows that this is a MIT Scratch project file. Cool.

Head over to the [Scratch editor](https://scratch.mit.edu/projects/editor/) and load the sb3 file given.

![scratch][scratch]

In the code above, we see that each time we click on the flag sprite, the flag will be appended with the new character. Translating this to Python gives:

```py
score = 0
aaa = "gdddbd0w2a3819y3d2390mcb}143748cb70{70"
flag = []
for i in range(len(aaa)):
    flag += aaa[(score % 38)]
    score += 1337

print(''.join(flag))
```

But after running it, I get `gwym7{b831bd23c47d1947dadb8009030d32}c` as the output. It looks random, but also kinda looks like a flag. Turns out I need to swap the positions of each 2 characters.

```py
score = 0
aaa = "gdddbd0w2a3819y3d2390mcb}143748cb70{70"
flag = []
for i in range(len(aaa)):
    flag += aaa[(score % 38)]
    score += 1337
    if i % 2 == 1:
        flag[-2], flag[-1] = flag[-1], flag[-2]
        print(''.join(flag))
# wgmy{78b13db324cd79174adbd089030d023c}
```

[challenge]:{{site.baseurl}}/ctfs/wargamesmy-21/capturetheflag/CTF.sb3
[scratch]:{{site.baseurl}}/ctfs/wargamesmy-21/capturetheflag/scratch.png