---
layout: post
title: Dumping x86 Assembly of C# DynamicMethod
---

This year, I managed to complete all Flare-On challenges (Flare-On 9). Yay. It is the first time I've done so, for the 4th year trying.

I believe everyone will say that challenge 8 is the toughest one. It gives a .NET executable, with most of its methods' IL (intermediate language) code being invalid, rendering dnSpy unable to decompile these methods. These IL code are only fixed during runtime by a proxy method, for the program to execute as intended.

![decompile-error][decompile-error]

There are 2 types of methods, and their names follow the same format. One starts with `flare_`, and another starts with `flared_`. For example, `flare_67` and `flared_67`. All the `flare_` methods have the following structure:

```cs
// FlareOn.Backdoor.FLARE15
// Token: 0x060000B5 RID: 181 RVA: 0x00013BF8 File Offset: 0x0001ABF8
public static object flare_67(byte[] b, int tk, object[] o)
{
	object obj;
	try
	{
		obj = FLARE15.flared_67(b, tk, o);
	}
	catch (InvalidProgramException ex)
	{
		obj = FLARE15.flare_71(ex, new object[] { b, tk, o }, FLARE15.cl_m, FLARE15.cl_b);
	}
	return obj;
}
```

The `flare_` methods are a wrapper/proxy of the `flared_` methods, which contain the actual program logic. However, all of the `flared_` methods have broken IL code, so dnSpy could not decompile them. By the same reason, when the `flare_` method calls them, an `InvalidProgramException` will be thrown, and `flare_71` is called to patch the IL code and execute it by giving the code to a `DynamicMethod` object.

For instance,
1. `flare_67` calls `flare_71`.
2. `flare_71` loads `flared_67`'s IL code into a bytearray.
3. `flare_71` patches the IL code.
4. `flare_71` creates a `DynamicMethod` object at gives it the patched IL code using `dynamicMethod.SetCode`.
5. `flare_71` executes the code body of `flared_67` by calling `dynamicMethod.Invoke`.


```cs
// FlareOn.Backdoor.FLARE15
// Token: 0x060000BC RID: 188 RVA: 0x00013EB8 File Offset: 0x0001AEB8
public static object flare_71(InvalidProgramException e, object[] args, Dictionary<uint, int> m, byte[] b)
{
    DynamicMethod dynamicMethod = new DynamicMethod("", methodInfo.ReturnType, array, declaringType, true);
	DynamicILInfo dynamicILInfo = dynamicMethod.GetDynamicILInfo();
	MethodBody methodBody = methodInfo.GetMethodBody();

	...

	dynamicILInfo.SetCode(b, methodBody.MaxStackSize);
	return dynamicMethod.Invoke(null, args);
}
```

I have truncated most of the code, of how the IL is patched, as this is not the point of this blog post. The important part is the last 2 lines, where the patched IL code is given to the `dynamicMethod` object (`b` is a bytearray of the patched code), which is then `Invoke`d.

In order for dnSpy to decompile these methods, the obvious solution is to patch their IL code in the executable, to a valid one. My immediate idea was to set a breakpoint before the `dynamicILInfo.SetCode` call in the snippet above, then copy and paste the contents of the `b` array into the executable, replacing the broken IL code.

However, it didn't fully work. dnSpy still throws a `DecompilerException`, saying:

```
 ---> System.Exception: Inconsistent stack size at IL_98
```

After reading the challenge author's writeup, I learnt that it is due to the difference between static and dynamic methods in .NET. However, I didn't know that during the challenge. I just felt very stuck. Until I came across the following readings that show me how I can debug .NET functions in WinDBG:

- [Flare-On 3: Challenge 9 Solution - GUI.exe](https://www.fireeye.com/content/dam/fireeye-www/global/en/blog/threat-research/flareon2016/challenge9-solution.pdf)
- [Viewing Emitted IL](https://web.archive.org/web/20190824082315/https://blogs.msdn.microsoft.com/curth/2008/08/12/viewing-emitted-il/)

According to these articles, the `DynamicMethod`s are JIT (just-in-time) compiled then executed, i.e. there is machine code for all of these methods. The disassembly of these machine code can be obtained using the `u` command in WinDbg. Instead of patching the broken IL code, I can instead read the disassembly of these methods. I thought it wouldn't be so long, so why not give it a try. And because of sunk-cost fallacy, I just went down this path of no return... of dumping and reading the disassembly of about 70 .NET methods 👍🙂

In this writeup, **I will not describe my solution for this challenge**. I just want to share how I dumped all the x86 assembly code of all `DynamicMethod` objects through WinDbg.

You may read the full writeup by the challenge author [here](https://www.mandiant.com/sites/default/files/2022-11/08-backdoor.pdf). The author, and other friends who have done this challenge, solved this challenge by patching the IL code of all methods in the executable. The writeup is a very good read to learn more about .NET internals.

Besides `flare_71` that does the patching and invocation of a `DynamicMethod` object, `flare_67` does so too. I won't go into the details of both. Just mentioning them for context.

## Breaking at the right place, at the right time

It actually was not easy at all to get the disassembly of all methods. I mentioned that I can get the disassembly. But here comes the difficult question: where are the jitted code of these methods located?

Here's a hint: they are associated with a `DynamicMethod` object, which is only allocated when the proxy methods (`flare_67` and `flare_71` are executed). The machine code is only present after the `DynamicMethod` is JIT compiled.

Recall that each `flared_` method is executed through its `flare_` wrapper function. An `InvalidProgramException` is thrown, and `flare_71` is called to fix the IL code and executed it through a `DynamicMethod`. The best place to start looking from is where `dynamicMethod.Invoke` is called. At some point within this function, the jitted code body of the `DynamicMethod` will be reached, and the disassembly can be obtained.

So, I want to set a breakpoint at `dynamicMethod.Invoke`. This is easy to do in dnSpy, but how about in WinDbg? It actually is not that hard too. I can get the disassembly of `flare_71` in WinDbg, and find the address where `Invoke` is called.

First, some setup. As an `InvalidProgramException` is thrown throughout the program, I had to set WinDbg to ignore some exception codes. I got these numbers from where WinDbg complains about them. It is not that important so I won't give more details.

```
sxi e0434352
sxi e06d7363
sxi 02345678
```

Then, the more useful setup. Set WinDbg to break (`sxe`) when the Common Language Runtime (CLR) is loaded (hence `ld:clr`). Then, call `.cordll -ve -u -l` to load this extension that gives extra commands for .NET executables.

```
sxe ld:clr
g
.cordll -ve -u -l
g
```

If you are a WinDbg noob like me, `g` means continue.

Now, I can use the `!Token2EE` command, to get the method's jitted code address. This command takes a method token, which can be obtained from dnSpy at the top of the method. E.g. `FlareOn.Backdoor.FLARE15.flare_71`'s token is `060000BC`.

```cs
// FlareOn.Backdoor.FLARE15
// Token: 0x060000BC RID: 188 RVA: 0x00013EB8 File Offset: 0x0001AEB8
public static object flare_71(InvalidProgramException e, object[] args, Dictionary<uint, int> m, byte[] b)
```

There are 2 ways of using the `!Token2EE` command, with or without the assembly name. Sharing both below for reference:

```
0:000> !token2ee * 060000bc
Module:      00007ffe8bc01000
Assembly:    mscorlib.dll
Token:       00000000060000bc
MethodDesc:  00007ffe8bee1520
Name:        Microsoft.Win32.Win32Native.SystemFunction041(System.Security.SafeBSTRHandle, UInt32, UInt32)
Not JITTED yet. Use !bpmd -md 00007ffe8bee1520 to break on run.
--------------------------------------
Module:      00007ffe2f564140
Assembly:    FlareOn.Backdoor.exe
Token:       00000000060000bc
MethodDesc:  <not loaded yet>
Name:        FlareOn.Backdoor.FLARE15.flare_71
Not JITTED yet.


0:000> !token2ee FlareOn.Backdoor.exe 060000bc
Module:      00007ffe2f564140
Assembly:    FlareOn.Backdoor.exe
Token:       00000000060000bc
MethodDesc:  <not loaded yet>
Name:        FlareOn.Backdoor.FLARE15.flare_71
Not JITTED yet.
```

Here we see that `FlareOn.Backdoor.FLARE15.flare_71` is `Not JITTED yet`, so the code doesn't exist in the process yet. In order to reach a point where the method is jitted, I can use the `!bpmd` command.

```
!bpmd FlareOn_Backdoor FlareOn.Backdoor.FLARE15.flare_71
```

Here's how it would look like in WinDbg.

```
0:000> !bpmd FlareOn_Backdoor FlareOn.Backdoor.FLARE15.flare_71
Found 1 methods in module 00007ffe2f564140...
Adding pending breakpoints...
0:000> g
ModLoad: 00007ffe`9e9f0000 00007ffe`9ea18000   C:\Windows\SYSTEM32\bcrypt.dll
ModLoad: 00007ffe`8a000000 00007ffe`8ac1b000   C:\Windows\assembly\NativeImages_v4.0.30319_64\System\556b21e2d636701016ad76fe3776a505\System.ni.dll
(dc0.2fc0): CLR notification exception - code e0444143 (first chance)
JITTED FlareOn.Backdoor!FlareOn.Backdoor.FLARE15.flare_71(System.InvalidProgramException, System.Object[], System.Collections.Generic.Dictionary`2<UInt32,Int32>, Byte[])
Setting breakpoint: bp 00007FFE2F687DC0 [FlareOn.Backdoor.FLARE15.flare_71(System.InvalidProgramException, System.Object[], System.Collections.Generic.Dictionary`2<UInt32,Int32>, Byte[])]
Breakpoint 0 hit
00007ffe`2f687dc0 90              nop


0:000> !token2ee FlareOn.Backdoor.exe 060000bc
Module:      00007ffe2f564140
Assembly:    FlareOn.Backdoor.exe
Token:       00000000060000bc
MethodDesc:  00007ffe2f565f88
Name:        FlareOn.Backdoor.FLARE15.flare_71(System.InvalidProgramException, System.Object[], System.Collections.Generic.Dictionary`2<UInt32,Int32>, Byte[])
JITTED Code Address: 00007ffe2f687d70
```

Now, there is a `JITTED Code Address`. We can click on the address in WinDbg, and it will help us call the `!U /d` command, which gives the disassembly.

```
0:000> !U /d 00007ffe2f687d70
Normal JIT generated code
FlareOn.Backdoor.FLARE15.flare_71(System.InvalidProgramException, System.Object[], System.Collections.Generic.Dictionary`2<UInt32,Int32>, Byte[])
Begin 00007ffe2f687d70, size ce9
>>> 00007ffe`2f687d70 55              push    rbp
00007ffe`2f687d71 57              push    rdi
00007ffe`2f687d72 56              push    rsi
00007ffe`2f687d73 4881ec40030000  sub     rsp,340h
00007ffe`2f687d7a c5f877          vzeroupper
00007ffe`2f687d7d 488dac2450030000 lea     rbp,[rsp+350h]
00007ffe`2f687d85 488bf1          mov     rsi,rcx
00007ffe`2f687d88 488dbdf0fcffff  lea     rdi,[rbp-310h]
00007ffe`2f687d8f b9c0000000      mov     ecx,0C0h
...
00007ffe`2f6889a4 e89703465d      call    mscorlib_ni!System.Reflection.Emit.DynamicILInfo.SetCode (00007ffe`8cae8d40)
00007ffe`2f6889a9 90              nop
00007ffe`2f6889aa 488b8d90feffff  mov     rcx,qword ptr [rbp-170h]
00007ffe`2f6889b1 4c8b4518        mov     r8,qword ptr [rbp+18h]
00007ffe`2f6889b5 33d2            xor     edx,edx
00007ffe`2f6889b7 3909            cmp     dword ptr [rcx],ecx
00007ffe`2f6889b9 e8b2f2ad5c      call    mscorlib_ni!System.Reflection.MethodBase.Invoke (00007ffe`8c167c70)
...
```

The end of the method is the interesting part, with calls to `SetCode` and `Invoke`. I can now set a breakpoint at `00007ffe2f6889b9`, which is right before calling `Invoke`, for my next step of reversing.

But before I continue, you may wonder. Can I just use `!bpmd` or `!Token2EE` on all the `flared` methods and easily get their disassembly? Unfortunately no. Because remember, they are called through a `DynamicMethod` (`SetCode` and `Invoke`), i.e. they are dynamically generated code. So, if we set a breakpoint on say `flare_67` with `!bpmd`, the breakpoint will never be hit, because the breakpoint is not set at the dynamically generated code.

Moving on, I know that at some point within `Invoke`, the jitted code of the `DynamicMethod` will be reached. For example, if `flare_67` calls `flare_71`, the jitted code of `flared_67` in the `DynamicMethod` will be reached, and I can get its disassembly.So, what better to do, than to set a breakpoint right before `Invoke` is called, and single step until I reach the jitted code.

Yes, really, that is what I did, for about 2 hours 👍🙂, using a nice combination of `t` (single step) and `gu` (step out). If you are interested, these are the functions that I encountered during the process. (Actually, in the end, none of these functions are relevant, just sharing here for those interested.)

```
clr!PreStubWorker
- clr!MethodDesc::CheckRestore
- clr!DoPrestub
 - clr!MethodTable::GetModule
 - clr!CheckRunClassInitThrowing
  - clr!IsClassPreInited
 - clr!MethodDesc::IsRestored
  - clr!IsILStub
 - clr!GetMethodEntryPoint
 - clr!Precode::GetTarget
 - clr!Precode::IsPointingToPrestub
  - clr!isJumpRel64
 - clr!PEFile::IsResource
 - clr!MethodTable::GetModule
 - clr!MethodDesc::MakeJitWorker
  - clr!GetAppDomain
  - clr!CrstBase::Enter
  - clr!!EEHeapAllocInProcessHeap
  - clr!CrstBase::Leave
  - clr!CrstBase::Enter
  - clr!CrstBase::Leave
  - clr!CrstBase::Enter
  - clr!ETW::MethodLog::MethodJitting
  - clr!UnsafeJITFunction
   - clr!EEJitManager::LoadJIT
   - clr!getMethodInfoHelper
    - clr!LCGMethodResolver::GetCodeInfo
     - clr!MethodDescCallSite::CallTargetWorker
      - clr!CallDescrWorkerWithHandler
       - clr!CallDescrWorkerInternal
        - mscorlib_ni!System.Reflection.Emit.DynamicResolver.GetCodeInfo
         - mscorlib_ni!System.Reflection.Emit.DynamicResolver.CalculateNumberOfExceptions
    - clr!LCGMethodResolver::GetLocalSig
     - clr!MethodDescCallSite::CallTargetWorker
      - clr!CallDescrWorkerWithHandler
   - clr!GetCompileFlags
   - clr!MethodDesc::LoadTypicalMethodDefinition
   - clr!ModifyCheckForDynamicMethod
    - clr!LCGMethodResolver::GetJitContext
     - clr!LCGMethodResolver::GetJitContextCoop
   - clr!GetCompileFlagsIfGenericInstatiation
   - clr!CallCompileMethodWithSEHWrapper
    - clr!invokeCompileMethod
     - clr!invokeCompileMethodHelper
      - clrjit!CILJit::compileMethod
       - clrjit!jitNativeCode
        - clrjit!Compiler::compCompile
         - clr!CEEInfo::getMethodClass
          - clr!LCGMethodResolver::GetJitContext
  - clr!ETW::MethodLog::MethodJitted
  - clr!DACNotifyCompilationFinished
 - clr!MethodDesc::GetMethodEntryPoint
 - clr!MethodDesc::DoBackpatch
- clr!InvokeUtil::CreateObject
 - clr!TypeHandle::GetSignatureCorElementType
  - clr!MethodTable::GetClass
 - clr!AllocateObject
 - clr!MethodTable::GetClass
- clr!HelperMethodFrame::Pop
- clr!HelperMethodFrameRestoreState
```

In the end, I found that `clr!ThePreStub+0x9d` is right before the jitted code body is reached. It is a `jmp rax` instruction, which makes a lot of sense, where `rax` contains the jitted code address.

```plaintext
0:000> u clr!ThePreStub+0x9d
clr!ThePreStub+0x9d:
00007ffe`8ee2e3ad 48ffe0          jmp     rax
```

Don't be surprised if the offset `0x9d` changes in the future. For a complete picture, this is the code inside `clr!ThePreStub`. The end of the function (`jmp rax`) is what we are interested in.

```plaintext
0:000> uf clr!ThePreStub
Flow analysis was incomplete, some code may be missing
clr!ThePreStub:
00007ffe`8ee2e310 4157            push    r15
00007ffe`8ee2e312 4156            push    r14
00007ffe`8ee2e314 4155            push    r13
00007ffe`8ee2e316 4154            push    r12
00007ffe`8ee2e318 55              push    rbp
00007ffe`8ee2e319 53              push    rbx
00007ffe`8ee2e31a 56              push    rsi
00007ffe`8ee2e31b 57              push    rdi
00007ffe`8ee2e31c 4883ec68        sub     rsp,68h
00007ffe`8ee2e320 48898c24b0000000 mov     qword ptr [rsp+0B0h],rcx
00007ffe`8ee2e328 48899424b8000000 mov     qword ptr [rsp+0B8h],rdx
00007ffe`8ee2e330 4c898424c0000000 mov     qword ptr [rsp+0C0h],r8
00007ffe`8ee2e338 4c898c24c8000000 mov     qword ptr [rsp+0C8h],r9
00007ffe`8ee2e340 660f7f442420    movdqa  xmmword ptr [rsp+20h],xmm0
00007ffe`8ee2e346 660f7f4c2430    movdqa  xmmword ptr [rsp+30h],xmm1
00007ffe`8ee2e34c 660f7f542440    movdqa  xmmword ptr [rsp+40h],xmm2
00007ffe`8ee2e352 660f7f5c2450    movdqa  xmmword ptr [rsp+50h],xmm3
00007ffe`8ee2e358 488d4c2468      lea     rcx,[rsp+68h]
00007ffe`8ee2e35d 498bd2          mov     rdx,r10
00007ffe`8ee2e360 e8aba3eaff      call    clr!PreStubWorker (00007ffe`8ecd8710)
00007ffe`8ee2e365 660f6f442420    movdqa  xmm0,xmmword ptr [rsp+20h]
00007ffe`8ee2e36b 660f6f4c2430    movdqa  xmm1,xmmword ptr [rsp+30h]
00007ffe`8ee2e371 660f6f542440    movdqa  xmm2,xmmword ptr [rsp+40h]
00007ffe`8ee2e377 660f6f5c2450    movdqa  xmm3,xmmword ptr [rsp+50h]
00007ffe`8ee2e37d 488b8c24b0000000 mov     rcx,qword ptr [rsp+0B0h]
00007ffe`8ee2e385 488b9424b8000000 mov     rdx,qword ptr [rsp+0B8h]
00007ffe`8ee2e38d 4c8b8424c0000000 mov     r8,qword ptr [rsp+0C0h]
00007ffe`8ee2e395 4c8b8c24c8000000 mov     r9,qword ptr [rsp+0C8h]
00007ffe`8ee2e39d 4883c468        add     rsp,68h
00007ffe`8ee2e3a1 5f              pop     rdi
00007ffe`8ee2e3a2 5e              pop     rsi
00007ffe`8ee2e3a3 5b              pop     rbx
00007ffe`8ee2e3a4 5d              pop     rbp
00007ffe`8ee2e3a5 415c            pop     r12
00007ffe`8ee2e3a7 415d            pop     r13
00007ffe`8ee2e3a9 415e            pop     r14
00007ffe`8ee2e3ab 415f            pop     r15
00007ffe`8ee2e3ad 48ffe0          jmp     rax
```

When the program reaches the `jmp rax` instruction, just single step (`t`) twice to reach the jitted code body, and get its disassembly (`!U /d rip`).

## Wrapping up: A simple example

Now, what's left is to set a breakpoint at this `jmp rax` instruction (`bu clr!ThePreStub+0x9d`), and single step (`t`) to the jitted code address, and get its disassembly (`!U /d rip`).

One important detail to note. Many of the CLR library functions reach `clr!ThePreStub+0x9d`, so remember to enable the breakpoint only when right before `Invoke` is called. Otherwise, you will reach the breakpoint so many times just to disassemble library code.

As shown above, there are quite a few steps needed to reach the `jmp rax` instruction. Also I didn't mention, but for 60 other methods in the executable, there are 2 stages of `DynamicMethod.Invoke`. Take `flare_51` for example:

1. `flare_51` calls `flare_67`.
1. `flare_67` calls `flare_71`.
1. `flare_71` loads `flared_67`'s broken IL code into a bytearray.
1. `flare_71` patches the IL code.
1. `flare_71` creates a `DynamicMethod` object at gives it the patched IL code using `dynamicMethod.SetCode`.
1. `flare_71` executes the code body of `flared_67` by calling `dynamicMethod.Invoke`.
1. `flared_67` loads `flared_51`'s broken IL code into a bytearray.
1. `flared_67` patches the IL code.
1. `flared_67` creates a `DynamicMethod` object at gives it the patched IL code using `dynamicMethod.SetCode`.
1. `flared_67` executes the code body of `flared_51` by calling `dynamicMethod.Invoke`.

Here is what the end of `flared_67` looks like (the same `SetCode` and `Invoke`):

```plaintext
00007ffb`72b338a8 e883bdf2ff      call    00007ffb`72a5f630 (System.Reflection.Emit.DynamicILInfo.SetCode(Byte[], Int32), mdToken: 00000000060048ea)
00007ffb`72b338ad 90              nop
00007ffb`72b338ae 488b8db0feffff  mov     rcx,qword ptr [rbp-150h]
00007ffb`72b338b5 4c8b4520        mov     r8,qword ptr [rbp+20h]
00007ffb`72b338b9 33d2            xor     edx,edx
00007ffb`72b338bb 3909            cmp     dword ptr [rcx],ecx
00007ffb`72b338bd e84ebef2ff      call    00007ffb`72a5f710 (System.Reflection.MethodBase.Invoke(System.Object, System.Object[]), mdToken: 00000000060045e2)
```

Here's what the call stack looks like when the jitted code of `flared_51` is reached. The call sites with addresses starting from `7ffe` (I've annotated below) are the jitted code bodies.

```plaintext
0:008> k
 # Child-SP          RetAddr               Call Site
00 00000059`38df66f8 00007ffe`8ee30e73     0x00007ffe`2f740590  <=== flared_51
01 00000059`38df6700 00007ffe`8ecf961b     clr!CallDescrWorkerInternal+0x83
02 00000059`38df6740 00007ffe`8ed11772     clr!CallDescrWorkerWithHandler+0x47
03 00000059`38df6780 00007ffe`8ed11b87     clr!CallDescrWorkerReflectionWrapper+0x1a
04 00000059`38df67d0 00007ffe`8cae9ee7     clr!RuntimeMethodHandle::InvokeMethod+0x3e7
05 00000059`38df6d00 00007ffe`8c167c92     mscorlib_ni!System.Reflection.Emit.DynamicMethod.Invoke+0xd7 [f:\dd\ndp\clr\src\BCL\system\reflection\emit\dynamicmethod.cs @ 744] 
06 00000059`38df6d80 00007ffe`2f74c482     mscorlib_ni!System.Reflection.MethodBase.Invoke+0x22 [f:\dd\ndp\clr\src\BCL\system\reflection\methodbase.cs @ 211] 
07 00000059`38df6dc0 00007ffe`8ee30e73     0x00007ffe`2f74c482  <=== flared_67
08 00000059`38df7110 00007ffe`8ecf961b     clr!CallDescrWorkerInternal+0x83
09 00000059`38df7150 00007ffe`8ed11772     clr!CallDescrWorkerWithHandler+0x47
0a 00000059`38df7190 00007ffe`8ed11b87     clr!CallDescrWorkerReflectionWrapper+0x1a
0b 00000059`38df71e0 00007ffe`8cae9ee7     clr!RuntimeMethodHandle::InvokeMethod+0x3e7
0c 00000059`38df7710 00007ffe`8c167c92     mscorlib_ni!System.Reflection.Emit.DynamicMethod.Invoke+0xd7 [f:\dd\ndp\clr\src\BCL\system\reflection\emit\dynamicmethod.cs @ 744] 
0d 00000059`38df7790 00007ffe`2f6989be     mscorlib_ni!System.Reflection.MethodBase.Invoke+0x22 [f:\dd\ndp\clr\src\BCL\system\reflection\methodbase.cs @ 211] 
0e 00000059`38df77d0 00007ffe`2f699d48     0x00007ffe`2f6989be  <=== flare_71
```

I don't know how to do scripting in WinDbg, so I just prepared a sequence of commands in VSCode, and paste all of them in at once. Here is the sequence of commands, with comments (lines starting with `*`).

```plaintext
* Setup 1: Ignore Exceptions
bc *
sxi e0434352
sxi e06d7363
sxi 02345678

* Setup 2: Load CLR debug extensions
sxe ld:clr
g
.cordll -ve -u -l
g
sxi ld:clr

* These are the parts of the challenge executable that are very slow but do nothing useful, e.g. sleeping/computing hashes.
* I patched them away with sleep(1) and nops.
!bpmd FlareOn_Backdoor FlareOn.Backdoor.FLARE11.flare_45
bm mscorlib_ni!System.Threading.Thread.Sleep "r rcx=1;g"
g
ed rip+2 90c88948
e rip+6 0x90
ed rip+7 0x90909090
bc 2

* Break at the target function flare_51
!bpmd FlareOn_Backdoor FlareOn.Backdoor.FLARE14.flare_51
g

* Break at the target function flare_67
* Then break at clr!ThePreStub+0x9d and step into flare_67's jitted code body
!bpmd FlareOn_Backdoor FlareOn.Backdoor.FLARE15.flare_67
g
bu clr!ThePreStub+0x9d
g
t
t

* Break at the call to Invoke in flare_67 (at offset 237d inside the method)
* Disable the clr!ThePreStub+0x9d breakpoint temporarily, to avoid library functions
bp rip+237d /1
bd 4
g

* When reached the Invoke call, enable the breakpoint again
* And step into the jitted code body of flare_51
be 4
g
t
t

* Cleanup: Remove and disable breakpoints
bc 5
bd 3-4

* Dump the disassembly of flare_51
!U /d rip
```

That's all. If you want to see the disassembly of all the methods in this challenge executable, [here they are](https://github.com/daniellimws/daniellimws.github.io/tree/master/stuff/flare-dis).


[decompile-error]:{{site.baseurl}}/images/dumping-csharp/decompile-error.png