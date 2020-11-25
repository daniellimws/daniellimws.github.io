---
layout: post
type: note
title: Building Ghidra from source
alias: tips
---

[Ghidra Developer's Guide](https://github.com/NationalSecurityAgency/ghidra/blob/master/DevGuide.md)

#### Clone the repo

```sh
git clone https://github.com/NationalSecurityAgency/ghidra.git
```

#### Fetch dependencies

```sh
gradle --init-script gradle/support/fetchDependencies.gradle init
```

*Note: After fetching the dependencies, it would be helpful to save backup of build/downloads, because it takes quite some time to download them.
This is because sometimes `gradle clean` is needed when checking out to a different commit, doing so will remove the downloaded files.*

#### Build Ghidra

```sh
gradle buildGhidra
````

This should take about 10 minutes.

#### Build Ghidra quickly

There are a couple of things that aren't needed when just building Ghidra for development purposes. The following build command skips the unneeded steps.

```sh
gradle buildGhidra -x ip -x createJavadocs -x createJsondocs -x zipJavadocs -x sleighCompile
```

*Note: Sometimes the `sleighCompile` step is needed. If Ghidra complains about Sleigh related errors then this step is most likely needed.*
#### Problem: Ghidra doesn't run properly

If Ghidra doesn't run properly after doing `gradle buildGhidra`, running `gradle clean` might get it to work.

`gradle clean` clears everthing, including the dependencies fetched earlier. To save time, copy *build/downloads* to another location, and copy it back after `gradle clean` is executed.
