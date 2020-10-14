import os
import firstspy

def execR(cmd):
    return os.popen(cmd).read().strip()

def execRL(cmd):
    res = os.popen(cmd).readlines()

    for i in range(len(res)):
        res[i] = res[i].rstrip()

    return res

def readFileLS(file):
    f = open(file, "r")

    fLines = f.readlines()

    for i in range(len(fLines)):
        fLines[i] = fLines[i].rstrip()
    
    return fLines

def main():
    estSources = firstspy.estimateSources(False)

    # Parse nodeDB
    nodes = readFileLS("db/nodes.db")
    nodeDB = {}
    for i in range(len(nodes)):
        nodes[i] = nodes[i].split("=")
        nodeDB[nodes[i][0]] = nodes[i][1]

    # Parse txDB
    txs = readFileLS("db/txs.db")
    txDB = {}
    for i in range(len(txs)):
        # print txs[i]
        txs[i] = txs[i].split(" ")
        # if(txs[i][1] in nodeDB):
        txDB[txs[i][0]] = nodeDB[txs[i][1]]

    # 
    # for eTx in estSources:
    #     print eTx+' : '+estSources[eTx]

    trues = 0
    falses = 0
    for tx in estSources:
        if tx in txDB:
            if estSources[tx]['src'] == txDB[tx]:
                print "CORRECT: "+tx
                trues+=1
            else:
                falses+=1

    rate = float(trues) / len(estSources)
    print "Correct: "+str(trues)+"  (Rate: "+ str(rate)+")"

main()