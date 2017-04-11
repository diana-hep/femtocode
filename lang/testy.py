# xdata = [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6]
# xsize = [3, 2, 2, 2, 3, 2, 2, 2]
# xdata = [1, 2, 3, 4, 5, 6]
# xsize = [3, 0, 0, 0, 3, 2, 2, 2]
xdata = [1, 2, 3, 4, 5, 6]
xsize = [0, 3, 2, 2, 2]

ydata = [1, 2, 3, 4, 5, 6, 7, 8]
ysize = [4, 4]

numEntries = 2
countdown = [0, 0, 0]
xdataindex = [0, 0, 0]
xsizeindex = [0, 0, 0]
ydataindex = [0, 0]
ysizeindex = [0, 0]
entry = 0
deepi = 0

xskip = [False, False]

while entry < numEntries:
    if deepi != 0:
        countdown[deepi - 1] -= 1

    if deepi == 0:
        xsizeindex[1] = xsizeindex[0]
        xdataindex[1] = xdataindex[0]
        countdown[deepi] = xsize[xsizeindex[1]]

        if xsize[xsizeindex[1]] == 0:
            xskip[0] = True
            countdown[deepi] = 1
        else:
            xskip[0] = False

        xsizeindex[1] += 1

    elif deepi == 1:
        xsizeindex[2] = xsizeindex[1]
        xdataindex[2] = xdataindex[1]
        countdown[deepi] = xsize[xsizeindex[2]]

        if xsize[xsizeindex[2]] == 0:
            xskip[1] = True
            countdown[deepi] = 1
        else:
            xskip[1] = False

        if not xskip[0]:
            xsizeindex[2] += 1

    elif deepi == 2:
        ysizeindex[1] = ysizeindex[0]
        ydataindex[1] = ydataindex[0]
        countdown[deepi] = ysize[ysizeindex[1]]
        ysizeindex[1] += 1

    elif deepi == 3:
        deepi -= 1
        print "{} ({}, {})".format(xskip, xdata[xdataindex[2]], ydata[ydataindex[1]])
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
            if not xskip[0] and not xskip[1]:
                xdataindex[2] += 1

    if deepi == 0:
        entry += 1
