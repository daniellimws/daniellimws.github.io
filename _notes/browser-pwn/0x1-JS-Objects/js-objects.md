---
layout: post
type: note
title: 0x1 - JS Objects
alias: v8
permalink: /notes/browser-pwn/0x1-js-objects
---

## References
* [Fast properties](https://v8.dev/blog/fast-properties)
* [Shapes and Inline Caches](https://mathiasbynens.be/notes/shapes-ics)

## 1. Object structure
A typical object in Javascript looks like in *Figure 1*, containing an `elements` and a `properties` array. Quite simple, `elements` is for indexed properties (e.g. `a[1]` and `a[100]`), whereas `properties` is for named properties (e.g. `a.apple` or `a.peanut`).

![](https://v8.dev/_img/fast-properties/jsobject.png)

<p align="center"><i>Figure 1. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

`Elements` is a typical array, where an element's index corresponds to its offset in memory. Though this is not always the case, when necessary (elements are sparse), a dictionary will be used instead.

On the other hand, `properties` is also an array, but requires additional metadata to deduce the location of a property. Such information is contained in a HiddenClass. The HiddenClass stores information about the "shape" of an object, and a mapping from property names to index in the `properties` array. Similar to `elements`, there are also cases where dictionary will be used instead of an array.

## 2. Properties
### 2.1 HiddenClasses and DescriptorArrays
Earlier, it was mentioned that HiddenClasses are used to store information about properties, such as property names and how to locate the property in memory.

![](https://v8.dev/_img/fast-properties/hidden-class.png)

<p align="center"><i>Figure 2. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

As seen in *Figure 2*, the first field of a JS object points to a HiddenClass. In the hidden class some metadata are stored, most notable is the third bit field, which stores the number of properties. 

Aside from that, the `DescriptorArray` would provide the greatest interest. It contains information about named properties like the name itself and the position where the value is stored. 

Obviously it would not be most efficient to create a new HiddenClass with the same properties when a new property is added to an object. v8 handles this situation by using "transitions", i.e. chain of HiddenClasses (*Figure 3*). When a new property is added to an object, a new HiddenClass is created but it only contains the new property. To retrieve information about the other properties, there is a link to the old HiddenClass, such link is called a transition. 

![](https://v8.dev/_img/fast-properties/adding-properties.png)

![](https://v8.dev/_img/fast-properties/transition-trees.png)

<p align="center"><i>Figure 3. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

### 2.2 Types of properties
Knowing the data structures involved in storing named properties, 3 different types of properties can be discussed.

#### 2.2.1 In-object property
Despite having a `properties` array, when there are very few properties (only 1 or 2), they are stored directly inside the object (refer to *Figure 4*), instead of the `properties` array. In this case, there is minimal indirection and hence the fastest.

#### 2.2.2 Normal property
Otherwise under a normal situation, properties will be stored in the `properties` store as shown in *Figure 4*.

Both **in-object properties** and **normal properties** are called **fast properties**, as they are relatively fast compared to **slow properties** described in *2.2.3*.

![](https://v8.dev/_img/fast-properties/in-object-properties.png)

<p align="center"><i>Figure 4. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

#### 2.2.3 Slow property
If many properties get added and deleted from an object, it can generate a lot of time and memory overhead to maintain the descriptor array and HiddenClasses. Hence, V8 also supports so-called slow properties. An object with slow properties has a self-contained dictionary as a properties store instead of an array (*Figure 5*). 

In this case, the HiddenClass and `DescriptorArray` are no longer used to maintain metadata about the properties as they are all stored in the dictionary. Such implementation does not support the usage of inline caches, hence it is very slow as compared to the aforementioned fast properties.

![](https://v8.dev/_img/fast-properties/fast-vs-slow-properties.png)

<p align="center"><i>Figure 5. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

### 3. Elements
Handling of integer-index properties is actually way more complex than it seems, as it turns out there are 20 different kinds of [elements](https://cs.chromium.org/chromium/src/v8/src/elements-kind.h?l=14&rcl=ec37390b2ba2b4051f46f153a8cc179ed4656f5d).

#### 3.1 Packed or Holey Elements
Sometimes in Javascript there will be "holes" in an array (e.g. `[1,,3]` or when an element is removed from the array). In this case, the JS engine will have to traverse the prototype chain to find out the value at this index (*Figure 6*), which affects performance. In memory, a hole is represented with a special constant called `the _hole`.

![](https://v8.dev/_img/fast-properties/hole.png)

<p align="center"><i>Figure 6. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

#### 3.2 Fast or Dictionary Elements
As a consequence, when the `elements` store is too sparse/holey, or when the indices are too large, v8 will switch to use a dictionary instead. Clearly it does not make sense to store 10000 holes.

#### 3.3 Smi and Double Elements
For fast elements there is another important distinction made in V8. For instance if there are only integers in an array, the GC does not have to look at the array, as integers are directly encoded as so called small integers (Smis) in place. 

Another special case are arrays that only contain doubles. Unlike Smis, floating point numbers are usually represented as full objects occupying several words. However, V8 stores raw doubles for pure double arrays to avoid memory and performance overhead. 
*Listing 1* shows 4 examples of Smi and double elements:

```js
const a1 = [1,   2, 3];  // Smi Packed
const a2 = [1,    , 3];  // Smi Holey, a2[1] reads from the prototype
const b1 = [1.1, 2, 3];  // Double Packed
const b2 = [1.1,  , 3];  // Double Holey, b2[1] reads from the prototype
```

<p align="center"><i>Listing 1. Source: <a href="https://v8.dev/blog/fast-properties">Fast Properties in v8</a></i></p>

#### 3.4 ElementsAccessor (Fun fact)
As mentioned earlier, there are 20 different types of elements in v8. How this is handled under the hood is quite interesting, with the use of [CTRP](https://en.wikipedia.org/wiki/Curiously_recurring_template_pattern), specialized versions of `Array` functions are created for the `ElementsAccessor`, instead of implementing the same function repeatedly.

Whenever an `Array` function is called, v8 dispatches through the `ElementsAccessor` to the specialized version of the function.

![](https://v8.dev/_img/fast-properties/elements-accessor.png)

## Additional Reading
* [What's up with monomorphism](https://mrale.ph/blog/2015/01/11/whats-up-with-monomorphism.html)