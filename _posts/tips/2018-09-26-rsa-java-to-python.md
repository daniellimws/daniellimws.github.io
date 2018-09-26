---
layout: post
title: Converting RSA encryption from Java to Python
---

Recently, when reversing an Android app, I stumbled across a request in their REST API that has a RSA encrypted string as a parameter.

### RSA encryption in Java

The following is the Java code used to encrypt the string.

```java
import javax.crypto.Cipher;
import java.security.Key;
import java.security.KeyPair;
import java.security.KeyFactory;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

public static byte[] encrypt(byte[] bArr) throws Throwable {
    Key generatePublic = KeyFactory.getInstance("RSA").
        generatePublic(new X509EncodedKeySpec(Base64.getDecoder().decode(public_key)));
    Cipher instance = Cipher.getInstance("RSA/ECB/PKCS1Padding");
    instance.init(1, generatePublic);
    return instance.doFinal(bArr);
}
```

As I wanted to send the request myself (not through the app) using Python, I need to have a function equivalent to the one above.

### RSA encryption in Python
To do this, I used the [`pycryptodome`](https://pycryptodome.readthedocs.io/en/latest/) library. The rest was quite straightforward, RSA using ECB and PKCS1 padding.

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64decode
from base64 import b64encode

def rsa_encrypt(s):
    key = b64decode(public_key)
    key = RSA.importKey(key)

    cipher = PKCS1_v1_5.new(key)
    ciphertext = b64encode(cipher.encrypt(bytes(s, "utf-8")))

    return ciphertext
```

(The `public_key` used in both the Java and Python code is the same base64 encoded string.)

However, a problem arose when trying to compare the outputs of the Java and Python code to ensure they are equivalent. This is because the PKSC1 padding [^1] attaches random characters to the end of the message, causing the ciphertext to be different every time.

The main reason I wanted to check is because the Java code uses `X509EncodedKeySpec` [^2] which I am not familiar with, and am unsure if it parses the key differently from my Python code that does not have any mention of `X509`.

[^1]: [PKSC1 padding](https://tools.ietf.org/html/rfc3447#section-7.2.1).

[^2]: [X509](https://en.wikipedia.org/wiki/X.509) is just the standard defining the format of public key certificates. The typical RSA key we see (starting with `-----BEGIN PUBLIC KEY-----`) falls into this category.

### RSA decryption in Python
I have no other choice than to first generate the ciphertext in Java, then decrypt it in Python and see if I get back the plaintext.

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64decode
from base64 import b64encode

def rsa_decrypt(s):
    key = open("key.pem").read()
    key = key.replace("-----BEGIN RSA PRIVATE KEY-----", "").replace("-----END RSA PRIVATE KEY-----", "").replace("\n", "")
    key = b64decode(key)
    key = RSA.importKey(key)

    cipher = PKCS1_v1_5.new(key)
    plaintext = cipher.decrypt(b64decode(s), "Error while decrypting")

    return plaintext
```

##### Generate RSA key pair using OpenSSL

Now, I can't use the public key used by the app since I do not have their private key to decrpyt the message. So, I had to generate my own RSA keypair.

First, generate the private key.

```sh
❯ openssl genrsa -out key.pem 2048
Generating RSA private key, 2048 bit long modulus
......................................................................................................................................................................................................................+++
........................+++
e is 65537 (0x010001)
```

Then, generate the public key from it.

```sh
❯ openssl rsa -in key.pem -outform PEM -pubout -out public.pem
writing RSA key
```

Now, I just need to change the Java code to use my generated public key. And yes, my Python code successfully decrypted the ciphertext by Java!

### Choice of encryption scheme
On a side note, it looks like Java is still using PKSC1 v1.5 which is prone to padding oracle attacks, instead of PKSC1 OAEP [^3]. But it does not really matter in the case of this app since this looks like just for preventing people from crafting their own requests. Nothing secretive in particular.

[^3]: [Optimal assymetric encryption padding](https://en.wikipedia.org/wiki/Optimal_asymmetric_encryption_padding)

***