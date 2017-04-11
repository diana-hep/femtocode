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

    xskip = [False, False]     # a skip for each variable,
    yskip = [False]            # length == depth of the progression

    while entry < numEntries:
        if deepi != 0:
            countdown[deepi - 1] -= 1

        if deepi == 0:
            xsizeindex[1] = xsizeindex[0]
            xdataindex[1] = xdataindex[0]

            if True:           # check all the x skips below this point
                countdown[deepi] = xsize[xsizeindex[1]]
                xsizeindex[1] += 1
            if True:           # check anything below this point
                outsize.append(countdown[deepi])

            if countdown[deepi] == 0:
                xskip[0] = True         # x and 0, like xsizeindex[0]
                countdown[deepi] = 1
            else:
                xskip[0] = False        # x and 0, like xsizeindex[0]

        elif deepi == 1:
            ysizeindex[1] = ysizeindex[0]
            ydataindex[1] = ydataindex[0]

            if True:           # check all the y skips below this point
                countdown[deepi] = ysize[ysizeindex[1]]
                ysizeindex[1] += 1
            if not xskip[0]:   # check anything below this point
                outsize.append(countdown[deepi])

            if countdown[deepi] == 0:
                yskip[0] = True         # y and 0, like ysizeindex[0]
                countdown[deepi] = 1
            else:
                yskip[0] = False        # y and 0, like ysizeindex[0]

        elif deepi == 2:
            xsizeindex[2] = xsizeindex[1]
            xdataindex[2] = xdataindex[1]

            if not xskip[0]:   # check all the x skips below this point
                countdown[deepi] = xsize[xsizeindex[2]]
                xsizeindex[2] += 1
            if not xskip[0] and not yskip[0]:     # anything below this point
                outsize.append(countdown[deepi])

            if countdown[deepi] == 0:
                xskip[1] = True         # x and 1, like xsizeindex[1]
                countdown[deepi] = 1
            else:
                xskip[1] = False        # x and 1, like xsizeindex[1]

        elif deepi == 3:
            deepi -= 1

            if not xskip[0] and not xskip[1] and not yskip[0]:
                               # check anything below this point
                outdata.append(xdata[xdataindex[2]] * 100 + ydata[ydataindex[1]])

            if not xskip[0] and not xskip[1]:     # x skips below this point
                xdataindex[2] += 1

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
                if not yskip[0]:                  # y skips below this point
                    ydataindex[1] += 1

        if deepi == 0:
            entry += 1

    return outdata, outsize

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [101, 201, 102, 202, 103, 203, 104, 204, 301, 401, 302, 402, 303, 403, 304, 404, 501, 601, 502, 602, 503, 603, 504, 604,
     705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208], \
    [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

assert testy([7, 8, 9, 10, 11, 12], [3, 0, 0, 0, 3, 2, 2, 2],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208], \
    [3, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

assert testy([7, 8, 9, 10, 11, 12], [0, 3, 2, 2, 2],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208], \
    [0, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

assert testy([1, 2, 3, 4, 5, 6], [3, 2, 2, 2, 3, 0, 0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [101, 201, 102, 202, 103, 203, 104, 204, 301, 401, 302, 402, 303, 403, 304, 404, 501, 601, 502, 602, 503, 603, 504, 604], \
    [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0])

assert testy([1, 2, 3, 4, 5, 6], [3, 2, 2, 2, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [101, 201, 102, 202, 103, 203, 104, 204, 301, 401, 302, 402, 303, 403, 304, 404, 501, 601, 502, 602, 503, 603, 504, 604], \
    [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 0])

assert testy([], [3, 0, 0, 0, 3, 0, 0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [], \
    [3, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 3, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0])

assert testy([], [0, 3, 0, 0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [], \
    [0, 3, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0])

assert testy([], [0, 0],
             [1, 2, 3, 4, 5, 6, 7, 8], [4, 4]) == (
    [], \
    [0, 0])

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [5, 6, 7, 8], [0, 4]) == (
    [705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208], \
    [3, 0, 0, 0, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [1, 2, 3, 4], [4, 0]) == (
    [101, 201, 102, 202, 103, 203, 104, 204, 301, 401, 302, 402, 303, 403, 304, 404, 501, 601, 502, 602, 503, 603, 504, 604], \
    [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 0, 0, 0])

assert testy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 2, 2, 2, 3, 2, 2, 2],
             [], [0, 0]) == (
    [], \
    [3, 0, 0, 0, 3, 0, 0, 0])

assert testy([7, 8, 9, 10, 11, 12], [3, 0, 0, 0, 3, 2, 2, 2],
             [5, 6, 7, 8], [0, 4]) == (
    [705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208], \
    [3, 0, 0, 0, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

assert testy([7, 8, 9, 10, 11, 12], [0, 3, 2, 2, 2],
             [5, 6, 7, 8], [0, 4]) == (
    [705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208], \
    [0, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

assert testy([7, 8, 9, 10, 11, 12], [0, 3, 0, 0, 0],
             [5, 6, 7, 8], [0, 4]) == (
    [], \
    [0, 3, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0])

assert testy([7, 8, 9, 10, 11, 12], [0, 0],
             [5, 6, 7, 8], [0, 4]) == (
    [], \
    [0, 0])
