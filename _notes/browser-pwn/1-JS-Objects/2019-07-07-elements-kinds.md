---
layout: post
type: note
title: 1.2 - Elements Kinds
alias: v8
permalink: /notes/browser-pwn/elements-kinds
---

## References
* [Elements Kinds in V8 (Matthias Bynes)](https://v8.dev/blog/elements-kinds)

## 0. Optimization for elements
Javascript objects have two types of attributes,
* `elements` - where the key is a numeric value, e.g. `a[1]`
* `properties` - where the key isn't a numeric value, e.g. `a['cool']`

V8 chooses to store them differently for optimization purposes.

## 1. Common element kinds
When running JS, V8 keeps track of the kind of elements an array contains. This information is for optimizing functions such as `reduce`, `forEach` or `map` called on an array. 

### 1.1 smi vs double vs regular elements
Observe the change in the array's elements kind as different types of values are added.

```js
const array = [1, 2, 3];
%DebugPrint(array);
```

```
▶ d8 --allow-natives-syntax packed-smi.js
DebugPrint: 0x5b808a8e0b9: [JSArray]
 - map: 0x3abb62702841 <Map(PACKED_SMI_ELEMENTS)> [FastProperties]
 - prototype: 0x345550306919 <JSArray[0]>
 - elements: 0x05b808a8e031 <FixedArray[3]> [PACKED_SMI_ELEMENTS (COW)]
 - length: 3
 - properties: 0x1807f3902d29 <FixedArray[0]> {
    #length: 0x1ae3f391c111 <AccessorInfo> (const accessor descriptor)
 }
 - elements: 0x05b808a8e031 <FixedArray[3]> {
           0: 1
           1: 2
           2: 3
 }
```

Here V8 marked the array as `PACKED_SMI_ELEMENTS`. The terms `packed` and `smi` are explained in the previous [note](js-objects#3-elements).

After adding a floating point literal to the array,

```js
const array = [1, 2, 3];
array.push(1.2);
%DebugPrint(array);
```

```
DebugPrint: 0x336e28e0e109: [JSArray]
 - map: 0x0f166f482931 <Map(PACKED_DOUBLE_ELEMENTS)> [FastProperties]
 - prototype: 0x066063206919 <JSArray[0]>
 - elements: 0x336e28e0e1e9 <FixedDoubleArray[22]> [PACKED_DOUBLE_ELEMENTS]
 - length: 4
 - properties: 0x323fa0782d29 <FixedArray[0]> {
    #length: 0x0f773331c111 <AccessorInfo> (const accessor descriptor)
 }
 - elements: 0x336e28e0e1e9 <FixedDoubleArray[22]> {
           0: 1
           1: 2
           2: 3
           3: 1.2
        4-21: <the_hole>
 }
```

Now the array is marked as `PACKED_DOUBLE_ELEMENTS`.

And now add a string literal,

```js
const array = [1, 2, 3];
array.push(1.2);
array.push('cool');
%DebugPrint(array);
```

```
DebugPrint: 0x336e28e0e109: [JSArray]
 - map: 0x0f166f4829d1 <Map(PACKED_ELEMENTS)> [FastProperties]
 - prototype: 0x066063206919 <JSArray[0]>
 - elements: 0x336e28e0e2a9 <FixedArray[22]> [PACKED_ELEMENTS]
 - length: 5
 - properties: 0x323fa0782d29 <FixedArray[0]> {
    #length: 0x0f773331c111 <AccessorInfo> (const accessor descriptor)
 }
 - elements: 0x336e28e0e2a9 <FixedArray[22]> {
           0: 0x336e28e0e399 <HeapNumber 1>
           1: 0x336e28e0e389 <HeapNumber 2>
           2: 0x336e28e0e379 <HeapNumber 3>
           3: 0x336e28e0e369 <HeapNumber 1.2>
           4: 0x066063223491 <String[4]: cool>
        5-21: 0x323fa0782691 <the_hole>
 }
```

The type of the array changes again, to `PACKED_ELEMENTS`.

Three types of elements are observed above:
* `Smi` - Small integers
* `Double` - For floating point representations and integers that cannot be represented as a `smi`
*  Regular elements - Anything that cannot be represented as `smi` or `double`

The types become more generic going down the list above, and the elements kind will be based on the most specific type that can represent all elements in the array. For example, for `[1, 1.1, 2, 3]` it will be `PACKED_DOUBLE_ELEMENTS` since `Double` is the most specific type to represent all elements.

Also, the conversion only goes one way. In the example above, the array turns from `PACKED_SMI_ELEMENTS` to `PACKED_DOUBLE_ELEMENTS` to `PACKED_ELEMENTS` but not the other way round.

### 1.2 `PACKED` vs `HOLEY` elements
Earlier, the arrays used are all packed. Creating holes in the array will downgrade it to its holey variant. E.g. `PACKED_SMI_ELEMENTS` to `HOLEY_SMI_ELEMENTS`.

```js
const array = [1, 2, 3];
array[5] = 5;
%DebugPrint(array);
```

```
▶ d8 --allow-natives-syntax holey-smi.js
DebugPrint: 0xefc2300e0c9: [JSArray]
 - map: 0x2ff055c028e1 <Map(HOLEY_SMI_ELEMENTS)> [FastProperties]
 - prototype: 0x3295a7a86919 <JSArray[0]>
 - elements: 0x0efc2300e0e9 <FixedArray[25]> [HOLEY_SMI_ELEMENTS]
 - length: 6
 - properties: 0x3e9121d02d29 <FixedArray[0]> {
    #length: 0x212d3b09c111 <AccessorInfo> (const accessor descriptor)
 }
 - elements: 0x0efc2300e0e9 <FixedArray[25]> {
           0: 1
           1: 2
           2: 3
         3-4: 0x3e9121d02691 <the_hole>
           5: 5
        6-24: 0x3e9121d02691 <the_hole>
 }
```

As seen here it is now `HOLEY_SMI_ELEMENTS` instead of `PACKED_SMI_ELEMENTS`.

The idea is that `PACKED` variants will transition to their `HOLEY` variants once there are holes in between elements of the array.

### 1.3 Elements kinds lattice
V8 implements this tag transitioning system as a lattice.

![elements kinds lattice](https://v8.dev/_img/elements-kinds/lattice.svg)
<p align="center"><i>Figure 1. Source: <a href="https://v8.dev/blog/elements-kinds">Elements Kinds in V8</a></i></p>

*Figure 1* shows the transitioning paths for the most common element kinds, and it is only possible to transition down the lattice (according to the arrows, e.g. from `PACKED_SMI_ELEMENTS` to `PACKED_DOUBLE_ELEMENTS` when there is a floating point representation added to the array). It is impossible to go backwards (e.g. from `HOLEY_SMI_ELEMENTS` to `PACKED_SMI_ELEMENTS`).

Currently, V8 distinguishes [21 different elements kinds](https://v8.dev/blog/elements-kinds).

```cpp
enum ElementsKind {
  // The "fast" kind for elements that only contain SMI values. Must be first
  // to make it possible to efficiently check maps for this kind.
  PACKED_SMI_ELEMENTS,
  HOLEY_SMI_ELEMENTS,

  // The "fast" kind for tagged values. Must be second to make it possible to
  // efficiently check maps for this and the PACKED_SMI_ELEMENTS kind
  // together at once.
  PACKED_ELEMENTS,
  HOLEY_ELEMENTS,

  // The "fast" kind for unwrapped, non-tagged double values.
  PACKED_DOUBLE_ELEMENTS,
  HOLEY_DOUBLE_ELEMENTS,

  // The "slow" kind.
  DICTIONARY_ELEMENTS,

  // Elements kind of the "arguments" object (only in sloppy mode).
  FAST_SLOPPY_ARGUMENTS_ELEMENTS,
  SLOW_SLOPPY_ARGUMENTS_ELEMENTS,

  // For string wrapper objects ("new String('...')"), the string's characters
  // are overlaid onto a regular elements backing store.
  FAST_STRING_WRAPPER_ELEMENTS,
  SLOW_STRING_WRAPPER_ELEMENTS,

  // Fixed typed arrays.
  UINT8_ELEMENTS,
  INT8_ELEMENTS,
  UINT16_ELEMENTS,
  INT16_ELEMENTS,
  UINT32_ELEMENTS,
  INT32_ELEMENTS,
  FLOAT32_ELEMENTS,
  FLOAT64_ELEMENTS,
  UINT8_CLAMPED_ELEMENTS,

  // Sentinel ElementsKind for objects with no elements.
  NO_ELEMENTS,

  // Derived constants from ElementsKind.
  FIRST_ELEMENTS_KIND = PACKED_SMI_ELEMENTS,
  LAST_ELEMENTS_KIND = UINT8_CLAMPED_ELEMENTS,
  FIRST_FAST_ELEMENTS_KIND = PACKED_SMI_ELEMENTS,
  LAST_FAST_ELEMENTS_KIND = HOLEY_DOUBLE_ELEMENTS,
  FIRST_FIXED_TYPED_ARRAY_ELEMENTS_KIND = UINT8_ELEMENTS,
  LAST_FIXED_TYPED_ARRAY_ELEMENTS_KIND = UINT8_CLAMPED_ELEMENTS,
  TERMINAL_FAST_ELEMENTS_KIND = HOLEY_ELEMENTS
};
```

### 1.4 Trace elements transitions
To observe the transitions that take place, there is the `--trace-elements-transitions` flag.

```js
const array = [1, 2, 3];
array[3] = 4.56;
array[4] = "Hello";
array[6] = 1;
```

```
▶ d8 --trace-elements-transitions trace-transitions.js
elements transition [PACKED_SMI_ELEMENTS -> PACKED_DOUBLE_ELEMENTS] in ~+40 at trace-transitions.js:2 for 0x2945aa18e0e1 <JSArray[3]> from 0x2945aa18e059 <FixedArray[3]> to 0x2945aa18e101 <FixedDoubleArray[22]>

elements transition [PACKED_DOUBLE_ELEMENTS -> PACKED_ELEMENTS] in ~+54 at trace-transitions.js:3 for 0x2945aa18e0e1 <JSArray[4]> from 0x2945aa18e101 <FixedDoubleArray[22]> to 0x2945aa18e1c1 <FixedArray[22]>

elements transition [PACKED_ELEMENTS -> HOLEY_ELEMENTS] in ~+70 at trace-transitions.js:4 for 0x2945aa18e0e1 <JSArray[5]> from 0x2945aa18e1c1 <FixedArray[22]> to 0x2945aa18e1c1 <FixedArray[22]>
```
