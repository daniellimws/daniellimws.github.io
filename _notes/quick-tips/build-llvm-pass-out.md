---
layout: post
type: note
title: Building LLVM passes out of the LLVM source tree
alias: tips
---

[Reference](https://llvm.org/docs/CMake.html#cmake-out-of-source-pass)

### Files

```
<project dir>/
    |
    CMakeLists.txt
    <pass name>/
        |
        CMakeLists.txt
        Pass.cpp
        ...
```

**\<project dir>/CMakeLists.txt**

```
cmake_minimum_required(VERSION 3.20)

project(InspectorPass)

# need at least c++11 to compile successfully, I chose c++17 just to be cool
set (CMAKE_CXX_STANDARD 17)

# maybe not needed, but just to be safe
set(CMAKE_C_COMPILER "clang")
set(CMAKE_CXX_COMPILER "clang++")

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# just copied from the docs
separate_arguments(LLVM_DEFINITIONS_LIST NATIVE_COMMAND ${LLVM_DEFINITIONS})
add_definitions(${LLVM_DEFINITIONS_LIST})
include_directories(${LLVM_INCLUDE_DIRS})

# this is very important, to link with the passes library
llvm_map_components_to_libnames(llvm_libs passes)

add_subdirectory(<pass name>)
```

**\<project dir>/\<pass name>/CMakeLists.txt**

```
add_library(LLVM<pass name> MODULE <pass name>.cpp)

# this is very important, to link with the passes library
target_link_libraries(LLVM<pass name> ${llvm_libs})
```

### Build

```sh
mkdir build && cd build
cmake -GNinja ..
ninja
```