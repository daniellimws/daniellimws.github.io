import string

cs = string.ascii_letters + string.digits + "{}_!@"

d = "2bb5a2eb68ebc96ec73198ae710522a4d0b0067e4279bccce7cdc1927ea989ee2bf743323f09b317eedf139ff8ae319fade4d3c0a4e60cd87e1e092dfa3a68f47eb66744a1fe247b12d4dd9988eedf13ac1b2348f59dd74f"
flag = ""

gdb.execute("gef config context.enable 0")
for i in range(len(d)//2):
    for c in cs:
        gdb.execute("run {} > /dev/null".format(flag + c))
        m = gdb.execute("x/bx $rsi+{}".format(i), to_string=True).strip().split(":\t0x")[1]
        if m == d[i*2:i*2+2]:
            flag += c
            print(flag)
            open("flag.txt", "w").write(flag)
            break
    