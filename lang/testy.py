numEntries = 2
in1 = [3, 2, 2, 2, 3, 0, 1, 2]
in2 = [4, 1]

entry = 0
in1i = [0, 0, 0]
in2i = [0, 0]
countdown = [None, None, None]
deepi = 0

newsize = []
dataLength = 0

while entry < numEntries:
    if deepi != 0:
        countdown[deepi - 1] -= 1

    if deepi == 0:
        deepi += 1
        in1i[1] = in1i[0]
        countdown[deepi - 1] = in1[in1i[1]]
        print "in1[", in1i[1], "]", in1[in1i[1]]
        newsize.append(in1[in1i[1]])
        in1i[1] += 1

    elif deepi == 2:
        deepi += 1
        in1i[2] = in1i[1]
        countdown[deepi - 1] = in1[in1i[2]]
        print "in1[", in1i[2], "]", in1[in1i[2]]
        newsize.append(in1[in1i[2]])
        in1i[2] += 1

    elif deepi == 1:
        deepi += 1
        in2i[1] = in2i[0]
        countdown[deepi - 1] = in2[in2i[1]]
        print "in2[", in2i[1], "]", in2[in2i[1]]
        newsize.append(in2[in2i[1]])
        in2i[1] += 1

    elif deepi == 3:
        dataLength += 1

    while deepi != 0 and countdown[deepi - 1] == 0:
        deepi -= 1
        if deepi == 0:
            in1i[0] = in1i[1]
            in2i[0] = in2i[1]
        elif deepi == 1:
            in1i[1] = in1i[2]
        elif deepi == 2:
            pass

    if deepi == 0:
        entry += 1
