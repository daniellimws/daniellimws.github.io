---
layout: post
title: simple-machine (re333)
ctf: CODEGATE Quals 2020
---

> Classic Check Flag Challenge Machine
>
> [simple_machine][simple_machine] [target][target]

We are given 2 files, [simple_machine][simple_machine] and [target][target]. We can execute `./simple_machine target` and the program will prompt for an input, and lets us know if it is equal to the flag. So **simple_machine** must be a virtual machine that executes the custom program contained inside **target**.

## Static Analysis
The main function is not very complicated, looks something like the following

```cpp
int main(int argc, char** argv) {
    char* target = new char[10000];
    // sets up an ifstream object and opens the file with the name `argv[1]`
    // reads the contents of the file into `target`
    ...

    Machine* machine = new Machine;
    setup_machine(machine, target);

    while(true) {
        something = get_something(machine);
        if (something == 0) break;
        do_something(machine);
    }

    // some cleanup code
    ...
}
```

The code for reading the contents of the file might look complex, with some C++ stuff going on. I did not spend too much time reversing that, but just set a breakpoint before `setup_machine(machine, target);` to check if `target` contains the contents of the chosen file, which is **target**. And yes it is, so no need to reverse.

Next is `setup_machine`. This function sets up the fields of `Machine` object, I think most likely a constructor since it is called right after `new`. Moving on, `get_something` returns the value of a field of `machine`, to determine when the loop should exit. 

The interesting function is `do_something`.

```cpp
void do_something(Machine *machine)

{
  FUN_555555555740(machine);
  if (machine->reg2 != '\0') {
    execute(machine);
  }
  if (machine->reg1 != '\0') {
    FUN_555555555560(machine);
  }
  FUN_555555555690(machine);
  return;
}
```

Clicking into the functions one by one, only `execute` is not complicated.

```cpp
void execute(Machine *machine)
{  
  short read_len, write_len;

  if (machine->opcode < 9) {
    switch(machine->opcode) {
    case 0:
      machine->res = machine->imm1;
      break;
    case 1:
      machine->res = machine->imm2 + machine->imm1;
      break;
    case 2:
      machine->res = machine->imm1 * machine->imm2;
      break;
    case 3:
      machine->res = machine->imm1 ^ machine->imm2;
      break;
    case 4:
      machine->res = machine->imm1 < machine->imm2);
      break;
    case 5:
      if (machine->imm1 != 0) {
        machine->reg1 = 0;
        machine->reg2 = 0;
        machine->reg3 = 0;
        *(machine->reg5 + 2) = machine->imm2;
        return;
      }
      break;
    case 6:
      read_len = read_input(machine,machine->imm1,&machine->imm2);
      machine->res = read_len;
      break;
    case 7:
      write_len = write(1, machine->imm1 + machine->code_ptr), machine->imm2);
      machine->res = write_len;
      break;
    case 8:
      machine->reg1 = 0;
      machine->reg2 = 0;
      machine->reg3 = 0;
      machine->reg4 = 0;
      return;
    }
  }
  machine->reg3 = 1;
  machine->field_0x3a = machine->field_0x31;
  machine->field_0x3c = machine->field_0x32;
  return;
}
```

I have no idea what the other functions do, and I don't really wanna know either. But this function `execute` definitely is the part that executes the code contained inside the file **target**. There are 9 instructions available, `assign`, `add`, `subtract`, etc, that operates on 2 immediate values and saves the result. I think the other complicated functions are to parse the contents of **target** and extract the instructions to be performed.

The offsets of the opcode, immediate values, and result are as shown in the following

```
opcode - 48
imm1 - 52
imm2 - 54
res - 62
```

## Extracting instructions
To obtain the instructions executed by the virtual machine, I made a script to set a breakpoint at the start of `execute` and print out the relevant fields of `machine`.

```cpp
# gdb -q -ex "source script" -ex "run target < input" ./simple_machine
set logging overwrite
set logging file dumped.txt
set logging redirect on
set logging on
gef config context.enable 0
break *0x00005555555557c0
commands 1
printf "opcode: 0x%hx\n", *(char*)($rdi+48)
printf "imm1: 0x%hx\n", *(short*)($rdi+52)
printf "imm2: 0x%hx\n", *(short*)($rdi+54)
printf "accum: 0x%hx\n", *(short*)($rdi+62)
c
end
```

To make things easy, I stored my input in a file, then just called the following command to run my script followed by running the program with my input.

```
gdb -q -ex "source script" -ex "run target < input" ./simple_machine
```

For every 2 bytes in the input, I got something that looked like the following.

```
...
Breakpoint 1, 0x00005555555557c0 in ?? ()
opcode: 0x3
imm1: 0x4141
imm2: 0x497d
accum: 0x497d

Breakpoint 1, 0x00005555555557c0 in ?? ()
opcode: 0x1
imm1: 0xcbf7
imm2: 0x083c
accum: 0x083c

Breakpoint 1, 0x00005555555557c0 in ?? ()
opcode: 0x4
imm1: 0x0
imm2: 0xd433
accum: 0xd433
```

Here `0x4141` is my input (`AA`). Referring to the pseudocode of `execute`, we can easily recognize that this is equivalent to 

```py
res = ((input ^ 0x497d) + 0xcbf7) < 0
```

What is left is to reverse this operation to get the correct 2 bytes of the input.

This process can be automated by extending the script to do this automatically for every 2 bytes in the input, but I am stupid so I just did it by hand to get the flag.


[simple_machine]:{{site.baseurl}}/ctfs/codegate-quals-20/simple-machine/simple_machine
[target]:{{site.baseurl}}/ctfs/codegate-quals-20/simple-machine/target