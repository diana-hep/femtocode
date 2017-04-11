def testy(xdata, xsize, ydata, ysize):
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

    xskip = [False, False]
    yskip = [False]

    while entry < numEntries:
        if deepi != 0:
            countdown[deepi - 1] -= 1

        if deepi == 0:
            xsizeindex[1] = xsizeindex[0]
            xdataindex[1] = xdataindex[0]

            if True:
                countdown[deepi] = xsize[xsizeindex[1]]
                xsizeindex[1] += 1
            if True:
                outsize.append(countdown[deepi])

            if countdown[deepi] == 0:
                xskip[0] = True
                countdown[deepi] = 1
            else:
                xskip[0] = False

        elif deepi == 1:
            xsizeindex[2] = xsizeindex[1]
            xdataindex[2] = xdataindex[1]

            if not xskip[0]:
                countdown[deepi] = xsize[xsizeindex[2]]
                xsizeindex[2] += 1
            if not xskip[0]:
                outsize.append(countdown[deepi])

            if countdown[deepi] == 0:
                xskip[1] = True
                countdown[deepi] = 1
            else:
                xskip[1] = False

        elif deepi == 2:
            ysizeindex[1] = ysizeindex[0]
            ydataindex[1] = ydataindex[0]

            if True:
                countdown[deepi] = ysize[ysizeindex[1]]
                ysizeindex[1] += 1
            if not xskip[0] and not xskip[1]:
                outsize.append(countdown[deepi])

            if countdown[deepi] == 0:
                yskip[0] = True
                countdown[deepi] = 1
            else:
                yskip[0] = False

        elif deepi == 3:
            deepi -= 1

            if not xskip[0] and not xskip[1] and not yskip[0]:
                outdata.append(xdata[xdataindex[2]] * 100 + ydata[ydataindex[1]])

            if not yskip[0]:
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

    return outdata, outsize

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [101, 102, 103, 104, 201, 202, 203, 204, 301, 302, 303, 304, 401, 402, 403, 404, 501, 502, 503, 504, 601, 602, 603, 604,
     705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208], \
    [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

assert testy([7, 8, 9, 10, 11, 12], [3, 0, 0, 0, 3, 2, 2, 2],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208], \
    [3, 0, 0, 0, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

assert testy([7, 8, 9, 10, 11, 12], [0, 3, 2, 2, 2],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208], \
    [0, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

assert testy([1, 2, 3, 4, 5, 6], [3, 2, 2, 2, 3, 0, 0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [101, 102, 103, 104, 201, 202, 203, 204, 301, 302, 303, 304, 401, 402, 403, 404, 501, 502, 503, 504, 601, 602, 603, 604], \
    [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 0, 0, 0])

assert testy([1, 2, 3, 4, 5, 6], [3, 2, 2, 2, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [101, 102, 103, 104, 201, 202, 203, 204, 301, 302, 303, 304, 401, 402, 403, 404, 501, 502, 503, 504, 601, 602, 603, 604], \
    [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 0])

assert testy([], [3, 0, 0, 0, 3, 0, 0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [], \
    [3, 0, 0, 0, 3, 0, 0, 0])

assert testy([], [0, 3, 0, 0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [], \
    [0, 3, 0, 0, 0])

assert testy([], [0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [], \
    [0, 0])

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [5, 6, 7, 8], [0, 4]) == (
    [705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208], \
    [3, 2, 0, 0, 2, 0, 0, 2, 0, 0, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [1, 2, 3, 4], [4, 0]) == (
    [101, 102, 103, 104, 201, 202, 203, 204, 301, 302, 303, 304, 401, 402, 403, 404, 501, 502, 503, 504, 601, 602, 603, 604], \
    [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 2, 0, 0, 2, 0, 0, 2, 0, 0])

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [], [0, 0]) == (
    [], \
    [3, 2, 0, 0, 2, 0, 0, 2, 0, 0, 3, 2, 0, 0, 2, 0, 0, 2, 0, 0])

assert testy([7, 8, 9, 10, 11, 12], [3, 0, 0, 0, 3, 2, 2, 2],
             [5, 6, 7, 8], [0, 4]) == (
    [705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208], \
    [3, 0, 0, 0, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

assert testy([7, 8, 9, 10, 11, 12], [0, 3, 2, 2, 2],
             [5, 6, 7, 8], [0, 4]) == (
    [705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208], \
    [0, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

assert testy([7, 8, 9, 10, 11, 12], [0, 3, 0, 0, 0],
             [5, 6, 7, 8], [0, 4]) == (
    [], \
    [0, 3, 0, 0, 0])

assert testy([7, 8, 9, 10, 11, 12], [0, 0],
             [5, 6, 7, 8], [0, 4]) == (
    [], \
    [0, 0])
