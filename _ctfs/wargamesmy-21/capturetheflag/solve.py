score = 0
aaa = "gdddbd0w2a3819y3d2390mcb}143748cb70{70"
flag = []
for i in range(len(aaa)):
    flag += aaa[(score % 38)]
    score += 1337
    if i % 2 == 1:
        flag[-2], flag[-1] = flag[-1], flag[-2]
        print(''.join(flag))
# wgmy{78b13db324cd79174adbd089030d023c}