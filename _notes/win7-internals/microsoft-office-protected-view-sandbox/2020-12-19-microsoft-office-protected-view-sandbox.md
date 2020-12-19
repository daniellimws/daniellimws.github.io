---
layout: post
type: note
title: Understanding the Microsoft Office Protected View Sandbox
permalink: win7-internals/microsoft-office-protected-view-sandbox
alias: win7-internals
---

> The following are my notes for the talk [Understaning the Microsoft Office Protected View Sandbox](https://www.youtube.com/watch?v=4Q1jFAc0Sec) by Koh Yong Chuan in REcon 2015.

## Outline

* Introduction
* Sandbox Internals
* Inter-Process Communication (IPC) Mechanism
* Microsoft Office 2016
* Conclusion

## Introduction

**Sandboxing 101:**

* A sandbox is a secirity mechansim for separating running programs
* Typically provides a tightly controlled set of resources for guest programs to run in
* Implemented by executing the software in a restricted operating system environment, thus controlling the resources that a process may use. Resources like:
  * File system
  * Registry
  * Process-related things

There might be things that the sandbox needs to do but not allowed to do. A request broker is used to work around these restrictions.

**Protected-View Sandbox:**
* Introduced since MS Office 2010
* Not used to view all files, but only untrusted files are rendered in sandbox. E.g. those downloaded from the Internet or attached as Outlook attachments
* Read-only mode. Disables any other unnecessary features for this purpose.

**Motivation:**
* Many excellent sandboxing researches
  * IE EPM
  * Chrome Sandbox
  * Adobe Reader
* No Protected-View publication since 2010
  * Community or MS

**Objective:**
* Find out more about the sandbox restrictions
* The list of tasks the broker could do in behalf of the sandbox, i.e. the IPC messages

**Disclaimer:** No 0-day in this presentation

## Sandbox Internals

* Architecture
* Initialization/Startup Process
* System Resource Restrictions

### Methodology

* "Sketch" the Protected-View sandbox architecture
* By comparing against IE sandbox model
  * Likelihood of code-reuse + components
  * Thoroughly researched by many

### Architecture

Typical IE sandbox architecture consisting of a higher privileged broker process:

![ie-sandbox][ie-sandbox]

In this model, 3 components are important:

* Interception component
* Elevation policy component
* IPC

#### Interception Component

* Used to redirect API calls
* In IE, this redirection facilitates 3 purposes:
  * Modify API parameters for the sandbox context. For example, original file path pointing to outside the sandbox directory will be modified to point to inside the sandbox directory.
  * Certain actions may need to be executed in the context of the broker.
  * Redirection may be forwarded to the **elevation policy component**.
* Implemented with API hooking (inline-hooking, IAT hooking or EAT hooking).
  * IE patches the IAT.
  * To find out whether the Protected-View sandbox has a similar component, the IAT and EAT were checked for patching.
  * Could not find any patching. It seems that the **interception component** is not present in **Protected-View**.

#### Elevation Policy Component

Since the **interception component** is not present, it is likely that the **elevation policy component** is not present as well, since both are related. Nonetheless, we will still do another check, from a different perspective.

In IE, elevation policies are stored as registry keys.
* `<AppName> | <AppPath> | <CLSID> | <LaunchPolicyValue>` format.
* The manager will check this registry to decide whether the requested process should be started.

So, the next step is to check for new registry keys with this format between **MS Office 2017** vs **MS Office 2013**. 2017 is the last version that doesn't implement Protected-View. Any new registry keys could be related to the sandbox. But no new registry in this format is found. So this component is not present.

#### IPC Component

This component is present. Only named-pipe IPC is present. More details later.

#### Final Protected-View sandbox

Should look like this:

![protected-view-sandbox][protected-view-sandbox]

This is hardly surprising given that this feature just needs to show the text contents of a file. Attack surface is greatly reduced. Especially due to the absence of the elevation policy component which has been commonly abused in IEPM escapes.

Notice that all untrusted files are rendered in the same sandbox process, so the broker will need a way to identify each file. More details later.

### Initialization

3 factors should be considered during the sandbox creation process:

* Restricted access token
* Should be created in an isolated windows station to minimize interaction with other process
* Access to resources should be restricted to its job handle

![][initialization]

![][initialization2]

![][initialization3]

2 modes the sandbox can be started:

* Low-Integrity mode for Win7
* AppContainer mode for Win8 and above

Refer to the *Orange* note at the bottom-right of the flowchart for how the system determines the mode.

* At the start, the sandbox name is only randomized at the last 10 bits.
* Then it sets the restrictions (refer to the green boxes). It does not do this all the time, by default there are no UI restrictions at all.
* Then it generates the Sandbox-SID and sets restrictions (refer to the orange boxes).
* Next, the broker creates the sandbox directory and grants access. If needed, the broker creates an isolated desktop (by default it doesn't).
* Then it sets up the IPC named-pipe with a buffer of 0x2000 bytes.
* Then the broker adds Office-Capability-SID if in AppContainer mode.
* Finally it creates the sandbox process.

From this, we see that the
* GUI sub-system is created without desktop isolation
* Job object has no UI restrictions
* Protected-view sandbox is vulnerable to the following known IEPM issues
  * Read/Write to clipboard, screen scraping, screen captures

### Restrictions

AppContainer is based on the concept known as capabilities, which defines the system resources that the sandbox can access. Defined in Winnt.h or regsitry keys.

But from the flowchart above, we see that only 1 capability is assigned:

* S-1-15-3-2929230137-1657469040
* Undocumented and unique to MS Office

To define the boundary of the sandbox container, we check for the sandbox capability-SIDs in the ACL in an iteration of file location and registry keys.

#### File locations

![][file-locations]

Sandbox-SID restricts access to **%UserProfile%\AppData\Local\Packages\<sandbox-name>** directory. Capability-SID does not allow access to any file locations. This is expected from the startup process.

#### Registry

![][registry.png]

Sandbox-SID restricts access to sandbox-related keys. Mostly with `KEY_ALL_ACCESS` access.

Capability-SID restricts access to Office-related registry keys. Only `KEY_READ` access.
* **HKCU\Software\Microsoft\Office\15.0\Word\Security\Trusted Locations** which defines the file path for which the Protected-View mode should be excluded.
* **HKCU\Software\Microsoft\Office\15.0\Word\File MRU** contains files that are recently opened in Office.

#### Network

Capbility-SID does not allow network outbound connections. Will return `WSAEACCES "Permission Denied"` error.

### Final illustration of sandbox internals

![][internals]

## IPC Mechanism used by Protected-View sandbox

* Internal Objects
* Format of IPC Messages
* Purpose of IPC Messages

### Internal Objects

(to be continued at 15:53)



[ie-sandbox]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/ie-sandbox.png
[protected-view-sandbox]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/protected-view-sandbox.png
[initialization]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/initialization.png
[initialization2]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/initialization2.png
[initialization3]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/initialization3.png
[file-locations]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/file-locations.png
[registry]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/registry.png
[internals]:{{site.baseurl}}/notes/win7-internals/microsoft-office-protected-view-sandbox/images/internals.png