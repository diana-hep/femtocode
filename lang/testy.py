xdata = [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6]
xsize = [3, 2, 2, 2, 3, 2, 2, 2]

# xdata = [1, 2, 3, 4, 5, 6]
# xsize = [3, 0, 0, 0, 3, 2, 2, 2]

# xdata = [1, 2, 3, 4, 5, 6]
# xsize = [0, 3, 2, 2, 2]

# xdata = []
# xsize = [0, 0]

ydata = [1, 2, 3, 4, 5, 6, 7, 8]
ysize = [4, 4]

# ydata = [5, 6, 7, 8]
# ysize = [0, 4]

outdata = []
outsize = []

numEntries = 2
countdown = [0, 0, 0]
xdataindex = [0, 0, 0]
xsizeindex = [0, 0, 0]
ydataindex = [0, 0]
ysizeindex = [0, 0]
entry = 0
deepi = 0

skip = [False, False]

while entry < numEntries:
    if deepi != 0:
        countdown[deepi - 1] -= 1

    if deepi == 0:
        xsizeindex[1] = xsizeindex[0]
        xdataindex[1] = xdataindex[0]
        countdown[deepi] = xsize[xsizeindex[1]]

        outsize.append(countdown[deepi])

        if countdown[deepi] == 0:
            skip[0] = True
            countdown[deepi] = 1
        else:
            skip[0] = False

        xsizeindex[1] += 1

    elif deepi == 1:
        xsizeindex[2] = xsizeindex[1]
        xdataindex[2] = xdataindex[1]

        if not skip[0]:
            countdown[deepi] = xsize[xsizeindex[2]]
            outsize.append(countdown[deepi])

        if countdown[deepi] == 0:
            skip[1] = True
            countdown[deepi] = 1
        else:
            skip[1] = False

        if not skip[0]:
            xsizeindex[2] += 1

    elif deepi == 2:
        ysizeindex[1] = ysizeindex[0]
        ydataindex[1] = ydataindex[0]
        countdown[deepi] = ysize[ysizeindex[1]]
        ysizeindex[1] += 1

        if not skip[0] and not skip[1]:
            outsize.append(countdown[deepi])

    elif deepi == 3:
        deepi -= 1
        if not skip[0] and not skip[1]:
            outdata.append(xdata[xdataindex[2]] * 100 + ydata[ydataindex[1]])
        ydataindex[1] += 1

    deepi += 1

    while deepi != 0 and countdown[deepi - 1] == 0:
        deepi -= 1

        if deepi == 0:
            xsizeindex[0] = xsizeindex[1]
            xdataindex[0] = xdataindex[1]
            ysizeindex[0] = ysizeindex[1]
            ydataindex[0] = ydataindex[1]

        elif deepi == 1:
            xsizeindex[1] = xsizeindex[2]
            xdataindex[1] = xdataindex[2]
            
        elif deepi == 2:
            if not skip[0] and not skip[1]:
                xdataindex[2] += 1

    if deepi == 0:
        entry += 1

print outsize
print outdata
