from pwn import xor

key = "19G)8U+"
with open("wordlist") as f:
    wl = f.read().rstrip().split("\n")

for i in wl:
    print(xor(i, key))