---
layout: post
title: simple python script (re750)
ctf: UTCTF 2019
---

> simple python script I wrote while not paying attention in graphics
> 
> by asper

[wtf.py][wtf]

We are given a python file with only 11 lines of code. Quite short isn't it?

![ss][ss]

This most likely have been generated using [onelinerizer](https://github.com/csvoss/onelinerizer). Check out the [talk](https://www.youtube.com/watch?v=DsUxuz_Rt8g) to know more about it. There is also a [website](https://onelinepy.herokuapp.com/) with demos.

In short, this script converts a python program into a single line using lambdas. For example, 

```py
def f(x):
    return x * 4
y = f(5)
print y
```

will be converted to

`(lambda __print, __g: [[(__print(y), None)[1] for __g['y'] in [(f(5))]][0] for __g['f'], f.__name__ in [(lambda x: (lambda __l: [(__l['x'] * 4) for __l['x'] in [(x)]][0])({}), 'f')]][0])(__import__('__builtin__', level=0).__dict__['print'], globals())`

Instead of diving right into reversing the whole long bunch of code, my attention was caught by the last few lines.

```py
# reformated for better readability
if getattr(__import__("difflib"), "SequenceMatcher")
   (None, 
    getattr(getattr(temp, "hexdigest")(), "lower")(),
    getattr(inputs[i // 5], "decode")("utf-8").lower()
   ).ratio() != 1.0: 
    exit()
```

This can be roughly translated to

```py
from difflib import SequenceMatcher
a = temp.hexdigest().lower()
b = inputs[i // 5].decode("utf-8").lower()
if SequenceMatcher(a, b).lower()).ratio() != 1.0:
  exit()
```

Now, the interesting part is to find out what `temp` and `inputs` are. We can check them by printing them before the `if` statement.

```
~/ctfs/utctf19/simplepy ➤ python3 wtf.py
> aaaa
temp: <sha1 HASH object @ 0x7fcff8c43300>
input: [b'26d33687bdb491480087ce1096c80329aaacbec7', b'1C3BCF656687CD31A3B486F6D5936C4B76A5D749', b'11A3E059C6F9C223CE20EF98290F0109F10B2AC6', b'6301CB033554BF0E424F7862EFCC9D644DF8678D', b'95d79f53b52da1408cc79d83f445224a58355b13']
``` 

After a few tries, we can tell that `inputs` is always the same regardless of our input.

Recall that the program is in a for loop.

```py
for i in range(0, len(flag), int((544+5j).imag)):
```

or

```py
for i in range(0, len(flag), 5):
```

and notice this on line 7

```py
getattr(temp, "update")(getattr(flag[i:i + 5], "encode")("utf-8"))
```

It is quite reasonable to say that the program takes 5 bytes of the input a time, and `temp` contains the sha1 hash of the 5-byte blocks. Quickly computing the sha1 hash of any string and passing it into the program verifies this assumption.

### Hash cracking
Now, we know that the program splits our input into 5-byte blocks, computes their sha1 hashes and then compares them with a pre-defined set of hashes.

I went to [crackstation](https://crackstation.net/), dumped all the hashes in `inputs`, and obtained the flag.

![crack][crack]

`puppyp1zzaanimetoruskitty`

[wtf]:{{site.baseurl}}/ctfs/utctf-19/simplepy/wtf.py
[ss]:{{site.baseurl}}/ctfs/utctf-19/simplepy/images/simplepy.png
[crack]:{{site.baseurl}}/ctfs/utctf-19/simplepy/images/crack.png

---