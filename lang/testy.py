numEntries = 2
in0 = [3, 2, 2, 2] * 2
in1 = [4] * 2

entry = 0
in0i = [0, 0, 0]
in1i = [0, 0]
countdown = [None, None, None]
deepi = 0

newsize = []
dataLength = 0

while entry < numEntries:
    if deepi != 0:
        countdown[deepi - 1] -= 1

    if deepi == 0:
        in0i[1] = in0i[0]
        countdown[deepi] = in0[in0i[1]]
        print "in0[", in0i[1], "]", in0[in0i[1]]
        newsize.append(in0[in0i[1]])
        in0i[1] += 1

    elif deepi == 1:
        in0i[2] = in0i[1]
        countdown[deepi] = in0[in0i[2]]
        print "in0[", in0i[2], "]", in0[in0i[2]]
        newsize.append(in0[in0i[2]])
        in0i[2] += 1

    elif deepi == 2:
        in1i[1] = in1i[0]
        countdown[deepi] = in1[in1i[1]]
        print "in1[", in1i[1], "]", in1[in1i[1]]
        newsize.append(in1[in1i[1]])
        in1i[1] += 1

    elif deepi == 3:
        deepi -= 1
        dataLength += 1

    deepi += 1

    while deepi != 0 and countdown[deepi - 1] == 0:
        deepi -= 1
        # print "deepi", deepi

        # #correct for in0, in0, in1
        # #correct for in0, in1, in0
        if deepi == 0:
            in0i[0] = in0i[1]
            in1i[0] = in1i[1]
        elif deepi == 1:
            in0i[1] = in0i[2]
        elif deepi == 2:
            pass

    if deepi == 0:
        entry += 1

def depth(size):
    return size.count("[]")

def generate(sizes):
    deepiToUnique = []
    uniques = []
    for size in sizes:
        if size not in uniques:
            deepiToUnique.append(len(uniques))
            uniques.append(size)
        else:
            deepiToUnique.append(uniques.index(size))

    totalDepth = sum(map(depth, uniques))
    assert totalDepth == len(sizes)

    params = ["numEntries"] + ["in{0}".format(i) for i in range(len(uniques))]

    init = ["entry = 0"]
    for i, size in enumerate(uniques):
        init.append("in{0}i = [{1}]".format(i, ", ".join(["0"] * (depth(size) + 1))))
    init.append("countdown = [{0}]".format(", ".join(["None"] * totalDepth)))
    init.append("deepi = 0")
    init.append("newsize = []")
    init.append("dataLength = 0")
    
    blocks = []
    reversals = dict((size, []) for size in uniques)
    uniqueDepth = [0] * len(uniques)

    for deepi in range(totalDepth):
        uniqueDepth[deepiToUnique[deepi]] += 1
        blocks.append("""if deepi == {deepi}:
            in{unique}i[{ud}] = in{unique}i[{udm1}]
            countdown[deepi] = in{unique}[in{unique}i[{ud}]]
            print "in{unique}[", in{unique}i[{ud}], "]", in{unique}[in{unique}i[{ud}]]
            newsize.append(in{unique}[in{unique}i[{ud}]])
            in{unique}i[{ud}] += 1
""".format(deepi=deepi,
           unique=deepiToUnique[deepi],
           ud=uniqueDepth[deepiToUnique[deepi]],
           udm1=(uniqueDepth[deepiToUnique[deepi]] - 1),
           ))

        reversal = "in{unique}i[{udm1}] = in{unique}i[{ud}]".format(
           unique=deepiToUnique[deepi],
           ud=uniqueDepth[deepiToUnique[deepi]],
           udm1=(uniqueDepth[deepiToUnique[deepi]] - 1),
           )

        reversals[uniques[deepiToUnique[deepi]]].insert(0, reversal)

    blocks.append("""if deepi == {0}:
            deepi -= 1
            dataLength += 1""".format(totalDepth))

    resets = []
    for deepi in range(totalDepth):
        revs = []
        for unique in uniques:
            if len(reversals[unique]) > 0:
                if deepi == 0 or sizes[deepi - 1] == unique:
                    revs.append(reversals[unique].pop())

        resets.append("if deepi == {deepi}:{revs}".format(
            deepi=deepi, revs="".join("\n                " + x for x in revs) if len(revs) > 0 else "\n                pass"))

    return """
def run({0}):
    {1}

    while entry < numEntries:
        if deepi != 0:
            countdown[deepi - 1] -= 1

        {2}

        deepi += 1

        while deepi != 0 and countdown[deepi - 1] == 0:
            deepi -= 1

            {3}

        if deepi == 0:
            entry += 1
""".format(", ".join(params),
           "\n    ".join(init),
           "\n        el".join(blocks),
           "\n            el".join(resets))
    
