---
layout: post
type: note
title: Building GDB with Python from source
alias: tips
---

[Documentation](https://sourceware.org/gdb/current/onlinedocs/gdb/Installing-GDB.html#Installing-GDB)

1. Download source [releases](https://ftp.gnu.org/gnu/gdb/)
2. Invoke the `configure` script
3. Run `make`

```sh
wget https://ftp.gnu.org/gnu/gdb/gdb-9.2.tar.xz
tar -xf gdb-9.2.tar.xz

cd gdb-9.2
mkdir build
cd build
../configure --with-python=/usr/bin/python3

make -j4
sudo make install
```

*Looks like in newer versions (10 onwards), we can run `configure` without creating a build folder.*