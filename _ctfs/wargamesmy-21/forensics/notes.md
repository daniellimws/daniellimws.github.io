### Forensic

```
root:forensics/ # sha256sum \[Job\ Application\]\ Security\ Engineer.eml
f4053a1aca84638b565c5f941a21b9484772520d7536e31ca41de0deaee14e2c  [Job Application] Security Engineer.eml
```

`wgmy{f4053a1aca84638b565c5f941a21b9484772520d7536e31ca41de0deaee14e2c}`

### Hash of Document

```
apt install -y mpack
munpack *.eml
```

```
root:forensics/ # sha1sum CV_Abdul_Manab.doc
706301fc19042ffcab697775c30fe7dd9db4c5a6  CV_Abdul_Manab.doc
```

`wgmy{706301fc19042ffcab697775c30fe7dd9db4c5a6}`

### API

`OtrpOlvrHtgdOt`: unhex

somehow this works

https://gchq.github.io/CyberChef/#recipe=From_Base64('A-Za-z0-9-_',true)Rotate_right(2,true)&input=SGFTZ2lOVEkzTnpOa00yUWlLU2tnSmlCRVlYa29kQ2tOQ2xCMWMyTkljbVZoSUQwZ1QyRnBiMVJ2YkdsVWIya29RM1JrWTBsd1pXSkJhMlZzUjJrb0lqVXlOemN6WkROa0lpa3BJQ1lnVFc5dWRHZ29kQ2tOQ2tWMVlXSk9hR3gwWVNBOUlGbGxZWElvZENrTkNrNWxjbXhVYm1OblJXNWhZbE5zWlhSbElEMGdVbWxuYUhRb1EyRm9hVVZ1TENBeUtTQW1JRTloYVc5VWIyeHBWRzlwS0VOMFpHTkpjR1ZpUVd0bGJFZHBLQ0kxTkRVeE0yUXpaQ0lwS1NBbUlGSnBaMmgwS0V4d2JISk5ZV1ZzVG1sd2FVWnVMQ0F5S1NBbUlGOE5DazloYVc5VWIyeHBWRzlwS0VOMFpHTko

and

`OaioToliToi` => https://gchq.github.io/CyberChef/#recipe=From_Hex('Auto')From_Base64('A-Za-z0-9-_',true)XOR(%7B'option':'UTF8','string':'wghykqpqxbpbusefktfw'%7D,'Standard',false)&input=NDU3ODQ5NDU0ODQ1NTU2OTQ2NTE0ZDRmNDM3ODRkNDg

somehow this works again (change rotate amount to 4)

https://gchq.github.io/CyberChef/#recipe=From_Base64('A-Za-z0-9-_',true)Rotate_right(4,true)&input=TndkR1JqWTJGeVlTQkJjeUJNYjI1bkRRcEVhVzBnUVhKaFkxSjFZWEJUYVcxeUxDQnBiblJsY2xaaGJIVmxJRUZ6SUZOMGNtbHVadzBLUkdsdElIUm9aVk4wWlhCaGN5QkJjeUJKYm5SbFoyVnlEUXAwYUdWVGRHVndZWE1nUFNCTVpXNG9SVzVuYmt4cFpXNHBJQ29nTWcwS1JHbHRJRlJ6WW1kTmNHRnlWV2x5Y3lCQmN5QlRkSEpwYm1jTkNsUnpZbWROY0dGeVZXbHljeUE5SUNJbVNDSU5Da1p2Y2lCRGNIUmtZMk5oY21FZ1BTQXhJRlJ2SUhSb1pWTjBaWEJoY3lCVGRHVndJRFFOQ2tGeVlXTlNkV0Z3VTJsdGNpQTlJRTFwWkVJb1JXNW5ia3hwWlc0c0lFTndkR1JqWTJGeVlTd2dOQ2tOQ2tGeVlXTlM

if doesnt work then try 6

### api

```
root:forensics/ # echo -n "urldownloadtofile" | sha1sum                                                                                                                                        [2:14:54]
c276cee25db80584ad8f07d39b683baf86a656aa  -
```

`wgmy{c276cee25db80584ad8f07d39b683baf86a656aa}`

### xor

```
root:forensics/ # echo -n "wghykqpqxbpbusefktfw" | sha1sum                                                                                                                                     [2:14:56]
23a00e2c2bd7e0b493384ea50cbf3e113ee0a1ba  -
```

`wgmy{23a00e2c2bd7e0b493384ea50cbf3e113ee0a1ba}`

### dropper

```
root:forensics/ # echo -n "http://mbnxosod7oj3lm5nky1u.for.wargames.my/cmd64.exe" | sha1sum                                                                                                    [2:15:43]
e88f4d8ad2551e5c91c742d53229944abd30c5ea  -
```

`wgmy{e88f4d8ad2551e5c91c742d53229944abd30c5ea}`

### malware hash

```
root:forensics/ # sha1sum cmd64.exe
094832f61127bbaaf9857d2e3ca6b3ffd3688e31  cmd64.exe
```

`wgmy{094832f61127bbaaf9857d2e3ca6b3ffd3688e31}`

### cmd64

`main`: 00401d30

http://unpyc.sourceforge.net/Opcodes.html

### encryption

```
~/ctfs/wargames21/forensics
❯ echo -n "K719HibejFfel6Jyl4A5TExmIUd2zLF7" | sha1sum
1d6d76404f85b440cf5db734af068a579915c9f2  -
```

`wgmy{1d6d76404f85b440cf5db734af068a579915c9f2}`

### hostname

```
~/ctfs/wargames21/forensics
❯ echo -n "wbgfcln.for.wargames.my" | sha1sum
7c7b739ef14c9f15f41ac73c8301eccd4de8ca9a  -
```

`wgmy{7c7b739ef14c9f15f41ac73c8301eccd4de8ca9a}`

### dga

use 7z to dump

```
root:soln/ # echo -n "whvrotw.for.wargames.my" | sha1sum                                                                                                               [10:40:24]
8ed3fad58dd5ce65528e787d49ea428dfa8b6632  -
```

`wgmy{8ed3fad58dd5ce65528e787d49ea428dfa8b6632}`