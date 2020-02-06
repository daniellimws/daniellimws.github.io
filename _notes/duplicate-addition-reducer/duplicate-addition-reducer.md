---
layout: post
type: note
title: 0x0 - Setting up
alias: dar
permalink: /notes/browser-pwn/duplicate-addition-reducer
---

```
fetch --nohooks chromium
cd src
build/install-build-deps.sh
gclient runhooks

git fetch --tags
git checkout tags/70.0.3538.9
gclient sync


gn gen out.dupadd/x64.debug
gn args out.dupadd/x64.debug

mkdir /vagrant/dup-add-red
cd /vagrant/dup-add-red
wget https://github.com/google/google-ctf/raw/master/2018/finals/pwn-just-in-time/attachments/addition-reducer.patch
wget https://github.com/google/google-ctf/raw/master/2018/finals/pwn-just-in-time/attachments/nosandbox.patch
```

