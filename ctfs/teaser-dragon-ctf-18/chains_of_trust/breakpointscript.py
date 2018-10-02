class DumpBreakpoint(gdb.Breakpoint):
    """Breakpoint to dump unpacked shellcode"""

    def __init__(self, location):
        super(DumpBreakpoint, self).__init__(location, gdb.BP_BREAKPOINT, internal=True, temporary=True)
        self.silent = True
        return

    def stop(self):
        return True


class BreakAndDumpCommand(GenericCommand):
    """Finds the call instruction in the shellcode binary, and sets a temporary breakpoint on it.
    Then, we can dump the 0x1000 bytes in the mmaped region
    """
    _cmdline_ = "break-and-dump"
    _syntax_  = "{} NAME".format(_cmdline_)

    def do_invoke(self, args):
        fpath = get_filepath()
        if fpath is None:
            warn("No executable to debug, use `file` to load a binary")
            return

        if not is_alive():
            err("gdb is not running")
            return

        disable_context()

        if len(args) != 1:
            err(self._syntax_)
            return

        number = gdb.parse_and_eval(args[0])
        name = "unpacked{}.dump".format(number)
        open("log", "a").write("{}: ".format(name))

        start_address = read_int_from_memory(get_register("rsp") + 0x20)
        mmap_memory = bytes(read_memory(start_address, 0x1000))

        addr = self.find_call_instruction(mmap_memory) + start_address

        # now we execute the binary to the point where the code is done unpacking
        DumpBreakpoint("*{:s}".format(hex(addr)))
        gdb.execute("c")

        if addr == None:
            err("GG can't find the call instruction. This shellcode must be different from the previous ones.")

        mmap_memory = bytes(read_memory(start_address, 0x1000))

        # replace strstr with atoi to bypass anti-debug
        mmap_memory = mmap_memory.replace(b"strstr", b"atoi\x00\x00")

        # check if its the errno one
        if b"errno" in mmap_memory:
            mmap_memory = mmap_memory.replace(b"\x48\x8B\x45\xF0\x8B\x00", b"\xb8\x01\x00\x00\x00\x90")

        # check if its the ptrace one
        if b"ptrace" in mmap_memory:
            mmap_memory = mmap_memory.replace(b"\x48\x83\xf8\xff\x75\x0b", b"\x48\x85\xc0\x90\x90\x90")
            mmap_memory = mmap_memory.replace(b"\x48\x83\xf8\xff", b"\x48\x85\xc0\x90")

        # ok just override the memory
        write_memory(start_address, mmap_memory, 0x1000)

        # code is unpacked, now dump it
        unpacked_address = addr + 5
        unpacked_address += read_memory(addr + 1, 1)[0]  # E8 offset 00 00 00
        info("Unpacked code is under {:s}".format(hex(unpacked_address)))

        gdb.execute("dump memory {} {} {}".format(name, hex(unpacked_address), hex(start_address + 0x1000)))
        info("Dumped unpacked code to {}".format(name))

        # if "Gynvael" is in memory, it means we have reached our destination
        if b"Gynvael" in mmap_memory:
            info("Main menu code!")
            open("log", "a").write("Main menu code!\n")

        # if "WoRK" is in memory, it means this code is useless
        elif b"WoRK" in mmap_memory:
            info("Useless code!")
            open("log", "a").write("Useless code!\n")

        # if "no debugging" is in memory, it means this code is useless
        elif b"No debugging" in mmap_memory:
            info("Anti-debugging code!")
            open("log", "a").write("Anti-debugging code!\n")

        else:
            info("Fresh code")
            open("log", "a").write("--- Fresh code! ---\n")

        # skip through executing it, none of my interest
        # multiple ni because gdb seems to screw up when doing finish straight away
        gdb.execute("ni")
        gdb.execute("ni")
        gdb.execute("ni")
        gdb.execute("ni")

        gdb.execute("finish")
        return

    def find_call_instruction(self, memory):
        """Searches in the .text section for the instruction that calls the unpacked code"""

        # first, we need to search for the first `mov rdx, rax`, because `call has only constant byte in its opcode,
        # and it is not reliable to search for it
        opcode = b"\x48\x89\xc2"
        last_found = -1  # Begin at -1 so the next position to search from is 0
        while True:
            # Find next index of opcode, by starting after its last known position
            last_found = memory.find(opcode, last_found + 1)
            if last_found == -1:
                break  # All occurrences have been found

            return last_found - 5

        return None

class SearchMatchingThread(GenericCommand):
    """Finds the call instruction in the shellcode binary, and sets a temporary breakpoint on it.
    Then, we can dump the 0x1000 bytes in the mmaped region
    """
    _cmdline_ = "find-thread"
    _syntax_  = "{} NAME".format(_cmdline_)

    # filenames = ["validator", "something4a", "actual_binary", "something22", "something31", "something3f"]

    def do_invoke(self, args):
        if len(args) != 1:
            err(self._syntax_)
            return

        filename = args[0]

        contents = open(filename, "rb").read()[: 100]
        vmmap = get_process_maps()
        start_addr = [x.page_start for x in vmmap if x.permission == 7][0]
        end_addr = [x.page_end for x in vmmap if x.permission == 7][-1]
        memory = read_memory(start_addr, end_addr - start_addr)
        for i in self.find_memory(memory, contents):
            gdb.execute("xinfo {}".format(hex(i + start_addr)))


    def find_memory(self, memory, target):
        last_found = -1
        while True:
            # Find next index of opcode, by starting after its last known position
            last_found = memory.find(target, last_found + 1)
            if last_found == -1:
                break  # All occurrences have been found

            yield last_found



if __name__ == "__main__":
    register_external_command( BreakAndDumpCommand() )
    register_external_command( SearchMatchingThread() )
