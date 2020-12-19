---
layout: post
type: note
title: Security in Windows Internals
permalink: win7-internals/security-in-windows-internals
alias: win7-internals
---

> The following are my notes for the video [Windows Internals by Alexander Sotirov](https://www.youtube.com/watch?v=vz15OqiYYXo).

The Windows OS architecture is well-designed. However, there might still be vulnerabilities in applications due to certain quirks of the API, or developers making mistakes because the API is not user-friendly.

## Windows Architecture

In UNIX systems, there is a clear separation between userland and kernel. But for Windows, there is no clear cut division. This is because there is no documentation for Windows kernel functions, and application developers cannot use them. Instead, Windows has dlls that provides functions that interfaces with the kernel, e.g. Win32, Kernel32 API. They call into NTDLL (a.k.a the native API), which contians very thin wrappers for kernel functions.

![smallimg][arch]

### C Runtime Library example

**MSVCR80.DLL**

```c
FILE *fopen(
    const char *filename,
    const char *mode
)
```

The parameters above are translated so that they can be passed into the following function provided by the Win32 API (KERNEL32.DLL):

```c
HANDLE CreateFileA(
  LPCSTR                lpFileName,
  DWORD                 dwDesiredAccess,
  DWORD                 dwShareMode,
  LPSECURITY_ATTRIBUTES lpSecurityAttributes,
  DWORD                 dwCreationDisposition,
  DWORD                 dwFlagsAndAttributes,
  HANDLE                hTemplateFile
);
```

We can call this function directly. It has more parameters, hence more power, but also more cumbersome. This function then uses the parameters given to call the following function in the Native API (NTDLL.DLL):

```c
__kernel_entry NTSTATUS NtCreateFile(
  PHANDLE            FileHandle,
  ACCESS_MASK        DesiredAccess,
  POBJECT_ATTRIBUTES ObjectAttributes,
  PIO_STATUS_BLOCK   IoStatusBlock,
  PLARGE_INTEGER     AllocationSize,
  ULONG              FileAttributes,
  ULONG              ShareAccess,
  ULONG              CreateDisposition,
  ULONG              CreateOptions,
  PVOID              EaBuffer,
  ULONG              EaLength
);
```

These functions (NT functions) are not supposed to be called by application developers. Originally, there were not documented, but because of some anti-monopoly things, Microsoft started to release documentation for some of them. Anyways, they were not meant to be called by users, because the underlying implementation in the kernel might change across versions.

Comparing this with UNIX syscalls, there is almost no translation of parameters that needs to be done, since the syscall is almost the same as the C function signature.

## Objects and Permissions

Almost everything in Windows on the lowest level is a *securable* object (i.e. all objects can have security permissions attached to them). For example, we can create a `Semaphore` and it can have certain permission settings.

![smallimg][object-types]

Comparing with UNIX, there is only RWX. On Windows, there is a richer set of permissions, for example:
* These users are allowed to write to this directory and its subdirectories, but another set of users can only write to this directories and not the subdirectories.
* There can also be groups, and permissions associated to each group.

So, the full set of permissions of a file can be really big. But there might be problems with this. Users/administrators/developers might not be aware of the full permissions of a file, which might result in certain security implications. On UNIX, this is less likely to happen, since `ls -la` will show us the permissions of each file. In Windows, we need to right click on a file, then click through a lot of dialogs to get the full picture.

### Insecure permissions

Since every object can be assigned with permissions, they might not be configured securely.

#### Service executables

There might be services running in the background, which are created by an executable, that is writable by the user. So, the user would have control over the service. Example situation: some developers made an installer to install a service to the background, but forgot to change the permissions of the file that creates those services, which can be quite common.

#### DLLs loaded by priviledged processes

Self-explanatory.

#### Registry keys with configuration settings
Sometimes, there would be services using configuration settings stored in the registry. The registry is also securable, so there can be permissions in the registry tree. A developer might forgot to set the permissions of certain registry keys, making it writable by any user.

#### Process and thread objects

Processes and threads are also securable. If permissions are not set correctly, threads might be accessible by any user. If a lower-privileged user has access to a higher-privileged thread, the user has control over the registers in the thread, including the instruction pointer, thus gaining control over program control flow.

#### Name squatting

Named pipes are used for client-server communications. A process (server) creates a pipe and gives it a name, then another process (client) connects to the pipe. *Client impersonation* is a mechanism that allows the server to get the client privileges, e.g. opening files with the privilege of the client. This is intended as a security feature, as this allows the server to be restricted to the same permissions as the client. E.g. if the client cannot access a file, the server also should not be able to access the file.

However, the problem comes when the client tries to connect to a named pipe that is not created yet. A low-privileged process can create a pipe with the same name, then impersonate the higher-privileged clients.

Microsoft has provided some APIs that make it easier to verify the server.

### Insecure Service Configuration

A service might look up a registry key to find the image path.

```
HKLM\SYSTEM\CurrentControlSet\Services\[service name]\Image Path
```

If not configured properly, a user has control over the `Image Path` key and point it to some other program.

### Unquoted service image path

Unquoted path in `CreateProcess`:

```
C:\Program Files\Vendor Name\Service.exe
```

Windows will need to figure out which part is the program name, and which part contains the arguments. So it will try the following one by one until it succeeds:

```
C:\Program.exe
C:\Program Files\Vendor.exe
C:\Program Files\Vendor Name\Service.exe
```

(In Windows we can omit the **.exe** to run a program)

It is probably not possible to create files in **C:\\** in modern versions of Windows, but this problem could still occur at a different location.

## DLL Loading

There might be problems that arise because of the way Windows search for a DLL. There has been problems in the past.

### Legacy DLL search order

Let's say a program tries to load a DLL with `LoadLibrary`, Windows will search for the DLL in the following order:

1. Executable directory
2. Current directory
3. C:\WINDOWS\System32
4. C:\WINDOWS\System
5. C:\WINDOWS
6. %PATH%

**There is a problem. The current directory is searched too early.**

Consider the following email, which contains a UNC path.

```plaintext
From: <alice@example.com>
To: <bob@example.com>

Hi Bob,

Please review the attached document:

\\1.2.3.4\share\document.xls

Thanks,
Alice
```

If the user clicks on the link attached, the system will try to connect to that IP with the Windows File Sharing Protocol, which also works over the Internet, to open the document. When the document opens, the **current directory** of Excel will be set to `\\1.2.3.4\share`. If the sender is malicious, there can be malicious DLLs in that directory that will be loaded by Excel.

#### Example: Safari carpet bombing attack

It was possible for a website to let Safari force-download a DLL file onto the user's desktop. Normally, there would be a popup that asks the user where to save the file after downloading. But Safari decided to make things easy and download things right into the default downloads folder, which is the desktop. This means that a website could drop any file onto someone's desktop. Developers decided that this was not a security threat.

Later, it was discovered that attackers could use Safari to drop a malicious DLL file onto a user's desktop. Then, if the user tries to open IE, which is saved as a shortcut on the desktop, IE will load the malicious DLL dropped onto the desktop.

### Safe DLL search order in XP SP2 and later:

1. Executable directory
2. C:\WINDOWS\System32
3. C:\WINDOWS\System
4. C:\WINDOWS
5. Current directory
6. %PATH%

**The current directory is moved to a later part of the search order.**

But there could still be a program with this. A program could be installed to load DLLs from **%PATH%**. An attacker could put malicious DLLs in the current directory.

Sometimes, a program may try to load DLLs that do not exist on the system, e.g. plugins. Failing to load such DLLs will not break the program. An attacker could identify such DLLs and create malicious versions of them. However, this is relatively rare to happen. Applications have also been hardened. For example, before loading a DLL (calling `LoadLibrary`), the application changes the **current directory** to a known safe directory, and change it back later to not interfere with the program execution.

## File path syntax

A web server might run into problems with this. For example, with **.\foo\../..\notepad.exe** as input:

If the current directory is **C:\Windows\System32**, the filename will be canonicalized to **C:\Windows\notepad.exe**.

### Trailing characters

These are equivalent:

* `"file.txt "`
* `"file.txt."`
* `"file.txt ... ....... ."`

Attacker can possibly do `GET /hidden.txt %20 HTTP/1.0` or `GET /hidden.txt. HTTP/1.0` to access **hidden.txt** which was not supposed to be allowed.

### Forward slashes

In **cmd.exe**, only backward slashes are accepted. However, actually the Win32 API accepts both forward slashes and back slashes.

Consider `GET \directory/hidden.txt HTTP/1.0`. A web server might only consider backward slashes, and try to compare `directory/hidden.txt` with `hidden.txt`, then open the file since it thinks that the path is valid.

### Alternate data streams

Windows supports alternate data streams in a file.

Syntax: `file.txt::[streamname]`

Sample usage: `type notepad.exe > file.txt::FOO`. This creates a file called **file.txt** and a stream called **foo**, which contains a copy of **notepad.exe**. This is a way to hide data.

However, the actual data of a file is always contained in the **\$DATA** stream (it is the default data stream). In IIS, doing `GET /scripts/login.asp HTTP/1.0` will execute the ASP script first, then send the result to the browser. However, in IIS4, doing `GET /scripts/login.asp::$DATA`, since the extension is not `.asp`, the ASP program will not be executed, instead the contents of the ASP source code will be sent to the browser.

### DOS 8.3 filenames

DOS filenames contain 8 characters as the file name, and 3 characters as the extension. For backwards compatability, Windows will give each file with a long name a truncated name. E.g. **C:\Program Files** becomes **C:\Progra~1**.

So, `GET \hidden~1.txt HTTP/1.0` can be used to get **hiddenfile.txt**.

This is still relevant in modern Windows systems (need to verify this on Windows 10).


[arch]:{{site.baseurl}}/notes/win7-internals/security-in-windows-internals/images/arch.png
[object-types]:{{site.baseurl}}/notes/win7-internals/security-in-windows-internals/images/object-types.png