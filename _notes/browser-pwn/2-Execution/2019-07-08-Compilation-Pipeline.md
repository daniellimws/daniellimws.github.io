---
layout: post
type: note
title: 2.0 - V8 Pipeline
alias: v8
permalink: /notes/browser-pwn/pipeline
---

## References
* [An Introduction to Speculative Optimization in V8 [Benedikt Meurer]](https://ponyfoo.com/articles/an-introduction-to-speculative-optimization-in-v8)
* [Ignition - an interpreter for V8 [Ross McIlroy]](https://www.youtube.com/watch?v=r5OWCtuKiAk&feature=youtu.be) ([slides](https://docs.google.com/presentation/d/1OqjVqRhtwlKeKfvMdX6HaCIu9wpZsrzqpIVIwQSuiXQ/edit#slide=id.gcd5fac7cb_3_11))
* [V8 pipeline [eternalsakura]](http://eternalsakura13.com/2018/09/05/pipeline/)

## 0. Compiler pipeline
![](https://cdn-images-1.medium.com/max/2400/1*GuWInZljjvtDpdeT6O0emA.png)
<p align="center"><i>Source: <a href="https://medium.com/reloading/javascript-start-up-performance-69200f43b201">JavaScript Start-up Performance by Addy Osmani</a></i></p>

Take the following function for example,

```js
function add(x, y) {
    return x + y;
}

for (var i = 0; i < 1000000; ++i) {
    add(1, 2);
}

add("hello", "world");
```

The `add` function was called so many times that V8 marks it as "hot". So *Turbofan* will come in to optimize this function and produce machine code. Since `add` has only been called with **smi** arguments, *Turbofan* can produce machine code that only works for small integers.

Later, `add("hello", "world")` was called. Now the arguments are no longer **smis**, hence the assumption that the arguments are **smis** is invalid, and so V8 will deoptimize and fall back to bytecode.

## 1. AST

## 2. Bytecode

## 3. Inline caches


[v8-old-pipeline]:{{site.baseurl}}/notes/browser-pwn/2-Execution/v8-old-pipeline.png
[v8-new-pipeline]:{{site.baseurl}}/notes/browser-pwn/2-Execution/v8-new-pipeline.png