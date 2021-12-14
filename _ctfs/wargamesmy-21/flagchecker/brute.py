import string
from binascii import unhexlify

cs = "abcdef" + string.digits + "{}_!@"
flag = "wgmy"

gdb.execute("gef config context.enable 0")
for i in range(4, 39):
    for c in cs:
        open("in", "w").write(flag + c)
        gdb.execute(f"run < in")
        # m = gdb.execute("x/bx $rsi+{}".format(i), to_string=True).strip().split(":\t0x")[1]
        m = read_memory(get_register("$rsi") + i, 1)
        correct = read_memory(get_register("$rdi") + i, 1)
        # print(i, c, m, correct)
        if m == correct:
            flag += c
            print(flag)
            open("flag.txt", "w").write(flag)
            break