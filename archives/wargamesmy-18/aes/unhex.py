import sys

n = sys.argv[1]

d = 0

for i in range(len(n)):
    mult = 16 ** (i + 1)
    d += float(int(n[i], 16)) / mult

print "%.18f" % d
