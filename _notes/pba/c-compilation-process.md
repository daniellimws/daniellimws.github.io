---
layout: post
type: note
title: The C Compilation Process
alias: pba
---

The compilation process can be split into 4 steps.

1. [Preprocessing Phase](#preprocessing-phase)
2. [Compilation Phase](#compilation-phase)
3. [Assembly Phase](#assembly-phase)
4. [Linking Phase](#linking-phase)

![compilation-process][compilation-process]

### Preprocessing Phase
In C, we can define our own macros or import external libraries using the `#define` and `#include` directives. This step expands these directives to prepare for the next step.

```c
#include <stdio.h>

#define MAGIC 999
#define p(n) printf("%d\n", n)

int main() {
    p(MAGIC);
    return 0;
}
```

Can be done with gcc using flags `-E` (for `gcc` to stop after preprocessing) and `-P` (to omit debugging information for cleaner output).

```bash
 ⚡ ➤ ~/pba/chapter1 ➤ gcc -E -P code.c

typedef long unsigned int size_t;
typedef unsigned char __u_char;
typedef unsigned short int __u_short;
typedef unsigned int __u_int;
typedef unsigned long int __u_long;
typedef signed char __int8_t;

/* ... */

extern int pclose (FILE *__stream);
extern char *ctermid (char *__s) __attribute__ ((__nothrow__ , __leaf__));
extern void flockfile (FILE *__stream) __attribute__ ((__nothrow__ , __leaf__));
extern int ftrylockfile (FILE *__stream) __attribute__ ((__nothrow__ , __leaf__)) ;
extern void funlockfile (FILE *__stream) __attribute__ ((__nothrow__ , __leaf__));

int main() {
    printf("%d\n", 999);
    return 0;
}
```

This step only imports the function declarations from the header files, not the function definitions.

### Compilation Phase
Compiles preprocessed code into assembly. Can be done with `gcc` using flags `-S` (to stop after compiling) and optional `-masm=intel` (to emit intel syntax).

```bash
 ⚡ ➤ ~/pba/chapter1 ➤ gcc -S -masm=intel code.c
 ⚡ ➤ ~/pba/chapter1 ➤ cat code.s
	.file	"code.c"
	.intel_syntax noprefix
	.text
	.section	.rodata
.LC0:
	.string	"%d\n"
	.text
	.globl	main
	.type	main, @function
main:
.LFB0:
	.cfi_startproc
	push	rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	mov	rbp, rsp
	.cfi_def_cfa_register 6
	mov	esi, 999
	lea	rdi, .LC0[rip]
	mov	eax, 0
	call	printf@PLT
	mov	eax, 0
	pop	rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.size	main, .-main
	.ident	"GCC: (Ubuntu 7.3.0-27ubuntu1~18.04) 7.3.0"
	.section	.note.GNU-stack,"",@progbits
```

### Assembly Phase
Compiles assembly code from compilation phase into object files containing machine code. Can be done with `gcc` using flags `-c` (to stop after assembly phase).

```bash
 ⚡ ➤ ~/pba/chapter1 ➤ gcc -c code.c
 ⚡ ➤ ~/pba/chapter1 ➤ file code.o
code.o: ELF 64-bit LSB relocatable, x86-64, version 1 (SYSV), not stripped
```

Notice the term *relocatable* in the output of `file`. Relocatable files don't rely on being placed at any particular address; rather, they can be moved around without breaking any assumptions in code. Object files need to be relocatable, because multiple object files will be linked together later to form an executable file.  

### Linking Phase
Final step of compilation. This step is performed by a linker. `gcc` goes through all steps of compilation (automatically calls the linker) by default so no flags are needed.

The object files from the previous step will be linked into an executable file. Definition of functions imported from external libraries (e.g. `printf`) will be added here if static linking is chosen. Static linking means definition of library functions will be packed into the executable; whereas for dynamic linking the libraries will only be loaded during runtime, taking up less space on the executable.

```bash
 ⚡ ➤ ~/pba/chapter1 ➤ gcc code.c
 ⚡ ➤ ~/pba/chapter1 ➤ file a.out
a.out: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=6c00f6b367f569278f6138d801c1c88a9fcdacbf, not stripped

 ⚡ ➤ ~/pba/chapter1 ➤ gcc code.c -no-pie
 ⚡ ➤ ~/pba/chapter1 ➤ file a.out
a.out: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=4ad2e3b0d0d6ecaf12cf7c966a00c3a104de41ce, not stripped
```

Modern versions of `gcc` will compile a C program into a position-independent executable (PIE), denoted as *shared object* in the output of `file`. This is done for security reasons. However, adding the `-no-pie` flag will tell `gcc` to not produce a PIE, and we will see *executable* in the output of `file` instead.

### Multiple files
The job of the linker can be better appreciated in a project with more than one source files.

```c
// code.c

#include <stdio.h>

#define MAGIC 999
#define p(n) printf("%d\n", n)

extern int foo(int);

int main() {
    p(foo(MAGIC));
    return 0;
}
```

```c
// extra.c

int foo(int a) {
    return a + 1;
}
```

In `code.c`, there is an external reference to `foo` that takes in an argument. The definition of `foo` can be found in `extra.c`.

Following the compilation process described earlier, we would preprocess, compile, then assemble each of the C files to obtain `code.o` and `extra.o`. At this point, `code.o` needs to call a function `foo`, but does not contain the definition, which can be found in `extra.o`. 

This is why object files need to be relocatable, as the addresses of some referenced data or functions are not yet known, so they contain *relocation symbols* that specify how function and variable references should eventually be resolved. 

During the linking step, the linker will combine all provided object files into an executable. Since this executable now contains the definition of `foo`, the call to `foo` in `main` can be resolved to a valid address.

```bash
 ⚡ ➤ ~/pba/chapter1 ➤ gcc extra.c code.c -o program
 ⚡ ➤ ~/pba/chapter1 ➤ file program
program: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=f1a67e6e3526b6a310e2813e9536cfa6048a40c7, not stripped
```

(This time, I added the `-o` flag that tells `gcc` the output name.)

---

#### References
1. Practical Binary Analysis - Chapter 1

[compilation-process]:{{site.baseurl}}/notes/pba/images/compilation-process.png