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
        txs[i] = txs[i].split(" ")
        if(txs[i][1] in nodeDB):
            txDB[txs[i][0]] = nodeDB[txs[i][1]]
        else:
            print "WARNING: missing: "+txs[i][0]

    # Compute overall
    trues = 0
    ptxs = 0
    for tx in estSources:
        if tx in txDB:
            ptxs+=1
            if estSources[tx]['src'] == txDB[tx]:
                trues+=1

    rate = float(trues) / float(ptxs)
    print "Overall Precision"
    print "Correct: "+str(trues)+" over "+str(ptxs)+" -- "+"Rate (overall): "+ str(rate)
    print " "

    # Compute proxytx only
    trues = 0
    ptxs = 0
    for tx in estSources:
        if (estSources[tx]['proxy']==True and tx in txDB):
            ptxs+=1
            if estSources[tx]['src'] == txDB[tx]:
                trues+=1
    
    if ptxs > 0:
        rate = float(trues) / float(ptxs)
        print "ProxyTx Precision"
        print "Correct: "+str(trues)+" over "+str(ptxs)+" -- "+"Rate (proxytx): "+ str(rate)

main()