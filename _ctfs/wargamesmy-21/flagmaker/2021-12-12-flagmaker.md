---
layout: post
title: flagmaker (re)
ctf: Wargames.MY 2021
permalink: /wargamesmy-21/flagmaker
---

[Challenge file][Challenge]

To run the challenge properly, we need to echo the input to a pipe to the binary.

```sh
$ echo wgmy | ./flagmaker

starting up the flag maker engine...
Initiating flag launching sequence...


ciphertext (hex):       DD38593C9D

plaintext:              wgmy

Flag launching sequence failed!
```

Otherwise, it will just get stuck here:

```sh
$ ./flagmaker

starting up the flag maker engine...
Initiating flag launching sequence...

```

### Static Analysis

I loaded the program in Ghidra to analyse it. `main` is not very big, but anyways it can be split into a few parts. Let's slowly go through each part.

#### Part 1: dmi stuff

```c
int main()
{
    if (s_03e7e303-8feb-c4fc-771c-3b13e8f2_0010e240[0] == '\0') {
        FUN_001027a9(s_03e7e303-8feb-c4fc-771c-3b13e8f2_0010e240);
    }
        FUN_0010288f(&DAT_0010e2e0,s_03e7e303-8feb-c4fc-771c-3b13e8f2_0010e240);
    if (s_e39c79ff9da51918_0010e270[0] == '\0') {
        FUN_001028f9(s_e39c79ff9da51918_0010e270);
    }
    FUN_00102a58(&DAT_0010e2c0,s_e39c79ff9da51918_0010e270);
```

Here, I see a GUID string being passed into some functions. Looking into these functions, I see references to strings like:

* `"/sys/devices/virtual/dmi/id/product_uuid"`
* `"dmidecode -s system-uuid"`
* `"/sys/devices/virtual/dmi/id/product_serial"`
* `"dmidecode -s system-serial-number"`
* `"/sys/devices/virtual/dmi/id/product_serial"`

All are related to `DMI`. I'm not familiar with this, but seems like it is related to `SMBIOS` (System Management `BIOS`). Not too sure what this is for, but I'll just keep this in mind for now, and move on.

#### Part 2: Decryption

Next, there's this series of function calls.

```c
    sVar3 = strlen(PTR_DAT_0010e288);
    local_440 = malloc(sVar3);
    sVar3 = strlen(PTR_DAT_0010e288);
    local_438 = malloc(sVar3);
    OPENSSL_init_crypto(2,0);
    OPENSSL_init_crypto(0xc,0);
    OPENSSL_init_crypto(0x80,0);
    sVar3 = strlen(PTR_DAT_0010e288);
    local_440 = (void *)FUN_00102d21(PTR_DAT_0010e288,sVar3 & 0xffffffff);        // [1]
    local_44c = FUN_00102c15(local_440,DAT_0010e220,&DAT_0010e2e0,&DAT_0010e2c0,local_438);       // [2]
```

Looking into `FUN_00102d21` (`[1]`), I see the `BIO_*` family of functions like `BIO_new`, `BIO_new_mem_buf`, `BIO_read`. `BIO` is openssl's I/O library, used to pass buffers from user code to openssl library for abstraction purposes.

In `FUN_00102c15` (`[2]`), I see the following calls:

1. `EVP_CIPHER_CTX_new`
2. `EVP_aes_256_cbc`
3. `EVP_DecryptInit_ex`
4. `EVP_DecryptUpdate`
5. `EVP_DecryptFinal_ex`
6. `EVP_CIPHER_CTX_free`

So AES decryption is happening here in this function. Also, usually `BIO_*` functions come right before `EVP_*` functions, being familiar with this pattern is helpful at identifying decryption routines quickly.

Renaming some stuff to make things clearer:

```c
    bio = malloc(len);

    len = strlen(encrypted);
    local_438 = malloc(len);

    OPENSSL_init_crypto(2,0);
    OPENSSL_init_crypto(0xc,0);
    OPENSSL_init_crypto(0x80,0);

    len = strlen(encrypted);
    bio = (void *)bio_setup(encrypted, len & 0xffffffff);

    local_44c = decrypt(bio, DAT_0010e220, &DAT_0010e2e0, &DAT_0010e2c0, local_438);
```

At the moment, I'm not too concerned about what is being decrypted and what the result is yet, so I note this down and continue.

#### Part 3: Fork and stuff

After decryption, there's code calling `mkfifo` (variables renamed for readability):

```c
    pid = getpid();
    sprintf((char *)&fifo_name,"/tmp/%i",(ulong)pid);
    result = mkfifo((char *)&fifo_name,0x1b6);
    if (result != 0) {
        unlink((char *)&fifo_name);
        result = mkfifo((char *)&fifo_name,0x1b6);
        if (result != 0) {
            printf("Aborting: could not create named pipe %s\n",&fifo_name);
            exit(1);
        }
    }
```

According to the `mkfifo` manpage:

> mkfifo() makes a FIFO special file with name pathname.  mode specifies the FIFO's permissions.

It's a file that is opened on both ends (input and output), and any process can open it to read/write to it. Well, sounds just like any other file. The benefit of using FIFO files is that it is never written to disk, so better performance in certain cases ([reference](https://unix.stackexchange.com/questions/433488/what-is-the-purpose-of-using-a-fifo-vs-a-temporary-file-or-a-pipe)).

Anyways, in the case of this binary, I just looked at it like a normal file, didn't care too much other than that.

Also, in the code, `mkfifo` is given `0x1b6` in the 2nd argument, which is the mode for opening the file. The number doesn't make much sense, but it should be just some enum. We can use `strace` to see the syscalls called by this program, if we're interested in the value (although it usually doesn't matter too much unless something totally unexpected happens).

```
$ strace ./flagmaker
...
getpid()                                = 10460
mknod("/tmp/10460", S_IFIFO|0666)       = 0
...
```

Above we see `getpid` followed by `mknod`, which matches the order of calls by the code we saw. But why `mknod` instead of `mkfifo`? This is because `mkfifo` is a C library function while `mknod` is a Linux syscall, and `strace` only logs syscalls. We see that `mknod` is called with the `S_IFIFO` enum which makes sense since `mkfifo` was called. The `0666` that follows should mean RW permissions.

These details aren't really important and I actually didn't care about them while reversing. Just noting them down for completeness sake. Moving on, we see the program `fork`s. From this point on, there are 2 processes running, the child process and the parent process.

There are 3 possible types of return values for `fork`:

* `-1` - failed
* `0` - we are in the child process
* positive value - we are in the parent process, and the return value is the child's process ID

The child doesn't need to get the parent's PID as return value, because it can call `getppid` to do so.

```c
    fork_pid = fork();
    if (fork_pid == -1) {   // failed fork
        puts("Error forking interpreter.");
    }
    else {
        if (fork_pid == 0) {    // child
            ...
        }
        else {                  // parent
            ...
        }
    }
```

The parent's code is shorter, so I looked at it first.

```c
    else {
        fifo_fd = open(fifo_name, 1);
        write(fifo_fd, local_438, local_44c);
        close(fifo_fd);
    }
```

So it's writing to the FIFO file. Recall that earlier `local_438` was passed to the `decrypt` function above, and `local_44c` was the return value. It is reasonable to assume that `local_438` contains the decrypted bufffer, and `local_44c` contains its length. I also verified it afterwards by looking into the `decrypt` function.

On the other hand, looking at the child process (renamed variables for better readability):

```c
    if (pid == 0) {
        command._0_8_ = 0;
        command._8_4_ = 0;
        command._12_2_ = 0;
        command[14] = '\0';
        exec_argv_ = exec_argv;
        exec_argv[0] = "bash";
        exec_argv[1] = "-c";
        sprintf(command, "source %s", &fifo_name);
        argv_ = argv;
        argc_ = argc;
        exec_argv_[2] = command;
        exec_argv_[3] = *argv;

        if (argc == 1) {
            local_408[0] = (char *)0x0;
        }
        else {
            for (i = 1; i < argc_; i = i + 1) {
                exec_argc[i + 3] = argv_[i];
            }
            exec_argc[i + 3] = (char *)0x0;
        }

        fflush(stdout);
        execvp("bash", exec_argv);
        puts("Interpreter crashed.");
    }
```

Here we see some notable things:

1. `execvp("bash", exec_argv);`
   1. This process will later be running `bash`, with some arguments set by the current process (child).
   2. With this call, we can deduce that the 2nd argument is an array of strings (as stated by the documentation of `execvp`).
2. `sprintf(command, "source %s", &fifo_name);`
   1. The format string strongly hints that this is the command passed to `bash` later.
   2. Especially since `"bash"` and `"-c"` are the strings that come before it in the argument list for `execvp`.
   3. We can expect `bash` to be called with the arguments above, `bash -c "source /tmp/<pid>"`.

At this point, we can see that this process will soon run a shell script contained in the FIFO file. That is where the flag checking logic is contained. So, we need to extract the shell script that is written to the FIFO file by the parent.

#### Part 4: Cleanup

Here's the remaining code for cleaning things up, which is really not important, but just here for completeness.

```c
    unlink(fifo_name);
    free(bio);
    free(decrypted);
    waitpid(pid, &result, 0);
    return 0;
```

### Interpreter

In order to extract the code written to the FIFO, one good way is to use GDB to set a breakpoint right after the file was written to.

```
00003f71 468    e8 ca e6        CALL       <EXTERNAL>::write
                ff ff
```

This binary is compiled with PIE on, so I use the `pie break` command by GEF. Since the contents of the file are in `$rsi`, I just do `x/s $rsi` to dump the file contents.

<script id="asciicast-NfSbjpxQb8mSTm1qFydrKIkyC" src="https://asciinema.org/a/NfSbjpxQb8mSTm1qFydrKIkyC.js" async></script>

And I get the following code:

```sh
#!/bin/bash
#wgmy{fakeflag}
oXePdudtpsYaUqiTsvJcvtgEuzDTiNZrxvUDvzxfOABOXnWxJywAkHSFoMvnLIoqXrIzudUSHiWdyMvhZvtBzJZdNFDbZumTtMBO="XoFkeEpMmBMXKNhQEAirSqHGPSMGXTxABZQxTJXLkSuRrEVKANlDcFbOgaCxTFrrSyqjvUQPnmCAYvpofRbJVSTtnYiaOCwYNZhU";
DCsdiTzmAWiSLTVwGdULBGAKcRTSNyXzsVtrBwjNFedTIoLWhDUKcyguyyWIYEBTdxmjlWovoaIypseNtCTJqLVOxtUendAdrImr="wMYbOjumSacDthPesvCHPQgcQxVlqMZgGiMZHFPoIUVorwPmmHEtGwmNzuzUDArAXgXzXknehmzLGukEBCKhSrFEXSDepPDfEYtu";
...
PqUfxGjNOXvQMGyONWnVzZQFaLjIfsJIUXuZLwZhiwzRedlbTFKgoldexofwTgtoqztvCXrQlYlEwtXptohITEhgNjJxcrdgrcvu="";
IeUouJEbKQKmvoXIAEgOjPnpXuqBZEcZwIvuLnUoTkMvDVcMTmPSXQEohwjCcFNrMyRbTwFpYBolIKWqhWcCGfJvbPCqJktyVBra=$(eval "$iHPaTqJxTbxmkvPCmSsRHNuaCJCdxMextIRBsGGkiFJVtGtdgOEHWMeiaYjrtcTPYpNexWavqMMnIogjAskkQHwaLaDFBrtlaAXQ$NXlVhgwGFHtNwpZvfCeKvmVEInIWdPLfkSrkHNQEVXhoaJdjzruCAljtqtjotgsNgaBRltBTOrKwdNpbEymKnsQZophyKwsSuGEw$BuGOClwGIsKErdKwgkfaJIUoTMqBgAEuyYykPYSkGUdiqkbuWSmKlhuWoZEeVLPaeloDYZHrBNTpxkIfRokkwIoZhCXAIjlebtXg$nANAiRZMluJPwrDmJXVJxDpkdIyYDtNidZfpAkKYtbatgUZtKMAhWlLPUdDtIvtGBgpvoqXgkcOZAHyqKpgegLEVOIxsTPylqOyX$YmXmADNUJnCCFYFtGEqxeANClYTGTptBhQWgmwtyYECLOrDrcFisFsJNPmxXttExEZWyqbKTayOAMyLBWimxvLDsbgrDopkBCFsX$tXdNfNAvEfMSRiflVLsssXYnHZvPEYuEbDIfKkEvuFZJspXSSSSmhrGLMbyRTrzoousnzieMNCUatRIOZUutfMYdBFxSiAtLFAhc$NXlVhgwGFHtNwpZvfCeKvmVEInIWdPLfkSrkHNQEVXhoaJdjzruCAljtqtjotgsNgaBRltBTOrKwdNpbEymKnsQZophyKwsSuGEw$jBQPrACikOnFetquFhFuJADpkJYDkOcRxnmdGZuVPXzhNbEFrRDlQiaexmmQKIVIxdwQBuJXsVnMVLehLPnjPRqKiREDVbTcbIKt$iHPaTqJxTbxmkvPCmSsRHNuaCJCdxMextIRBsGGkiFJVtGtdgOEHWMeiaYjrtcTPYpNexWavqMMnIogjAskkQHwaLaDFBrtlaAXQ$HXgOinAkfKiOLyRTwIuZntVONhuTspOunIKyxzerUgEFfsZNxAmJOnYsQsAMsJRJYytBTzjSccTmdEzrEMjkHziSsoJqGidicise$PqUfxGjNOXvQMGyONWnVzZQFaLjIfsJIUXuZLwZhiwzRedlbTFKgoldexofwTgtoqztvCXrQlYlEwtXptohITEhgNjJxcrdgrcvu$eRMfCTdAUETFQotxXrGeVAecLRiexuvbHkOBrYnJODGzCcNWdXsECdcpGAyHnHEGXQETRxuFJnchBofIcyKgxqpClTfOzGgEOJVZ$NXlVhgwGFHtNwpZvfCeKvmVEInIWdPLfkSrkHNQEVXhoaJdjzruCAljtqtjotgsNgaBRltBTOrKwdNpbEymKnsQZophyKwsSuGEw$LCwufSJHfbbfcCoHnWnuInsZzxQFtmmYvUseWTQesiMFfkxGobcRSoNOJciyXtbapcorJzfZVuCqCoGAyUbaqYopmOkslvxZYsFD$nANAiRZMluJPwrDmJXVJxDpkdIyYDtNidZfpAkKYtbatgUZtKMAhWlLPUdDtIvtGBgpvoqXgkcOZAHyqKpgegLEVOIxsTPylqOyX$QowYPStjYiAFkoRypHbbxojkFUYpCeRsMRtzfOkDqbhmjoMyYzsqMErIqjdkWkEvMLrvRxirLYoDOFsQHZWBpKmVAAsaoZVtisdP$ZeBDEsGcNquygsskARcDEaXtGwRDWNFGNrOEpeoQOOnUDSAYeUfJAsNbPTuWBHaPJAUYOBUnZdmuUgHxvmzZTXdTNZjptKQihfCI$PqUfxGjNOXvQMGyONWnVzZQFaLjIfsJIUXuZLwZhiwzRedlbTFKgoldexofwTgtoqztvCXrQlYlEwtXptohITEhgNjJxcrdgrcvu");
eval "$OqgaqMOsTruvyVZJTgiWVDClvZqNKXAjQKsAhghwVlJJOfmuKJzbfvCGHeVBxepPtqEtQOYEmBDNFgzRtgzYRHbrHOeuJTLqBDcC$IeUouJEbKQKmvoXIAEgOjPnpXuqBZEcZwIvuLnUoTkMvDVcMTmPSXQEohwjCcFNrMyRbTwFpYBolIKWqhWcCGfJvbPCqJktyVBra$iHPaTqJxTbxmkvPCmSsRHNuaCJCdxMextIRBsGGkiFJVtGtdgOEHWMeiaYjrtcTPYpNexWavqMMnIogjAskkQHwaLaDFBrtlaAXQ$nANAiRZMluJPwrDmJXVJxDpkdIyYDtNidZfpAkKYtbatgUZtKMAhWlLPUdDtIvtGBgpvoqXgkcOZAHyqKpgegLEVOIxsTPylqOyX"
```

Nasty. But notice at the last line, it runs `eval` on code stored in some variable. I just change the `eval` to `echo`, to see what's the code being executed.

And I got the following:

```sh
#!/bin/bash
################################################################################
# file:         rc4.sh
# created:      15-05-2011
# modified:     2014 Sep 04
#
# https://secure.wikimedia.org/wikipedia/en/wiki/RC4
#
# NOTES:
#   - ord() & chr() from http://mywiki.wooledge.org/BashFAQ/071
#
# TODO:
#   - todo figure out a better way for all the conversions
#   - optimize =)
#   - improve the s-box drawing thingie to only print changed bytes
#
################################################################################
set -u
shopt -s nocasematch
declare     TITLE="rc4.sh -- the RC4 stream cipher"
declare -a  S=()
declare -ai KEY=()
declare -i  KEYLENGTH
# Two 8-bit index-pointers
...
```

Scrolling through the code, I see 2 interesting parts. I can ask use the script to decrypt

```sh
        options:
          -d            decrypt (the default is to encrypt)
          -h            this help
          -k key        key
                        you can provide the key as hex by prefixing with '0x',
                        it is otherwise interpreted as ASCII.

          -x            debug mode
```

and also here I see the expected ciphertext

```sh
  if [ ${CIPHERTEXT^^} == "DD38593CEC368BE7DFC709E59A4878F7C462D6BD6E128515B39CCE1E94012814C056821E976D" ]
  then
    printf "Flag has been launch!!!! Submit your flag\n\n"
  else
    printf "Flag launching sequence failed!\n\n"
  fi
```

Only thing left is to run the script with `-d` and give it the ciphertext. And here's the flag:

```sh
$ echo -n "DD38593CEC368BE7DFC709E59A4878F7C462D6BD6E128515B39CCE1E94012814C056821E976D" | ./rc4.sh -d

starting up the flag maker engine...
Initiating flag launching sequence...


plaintext:      wgmy{57da7e9e691d02a99b6116be6156927b}
```



[challenge]:{{site.baseurl}}/ctfs/wargamesmy-21/flagmaker/flagmaker