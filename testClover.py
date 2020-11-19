import sys
import os
import time
import re
import glob
import json
import datetime

import btcnet

def parseDate(str):
    return datetime.datetime(int(str[0:4]),int(str[5:7]),int(str[8:10]),int(str[11:13]),int(str[14:16]),int(str[17:19]),int(str[20:26]))

class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime.datetime):
            return (str(z))
        else:
            return super().default(z)

def printDB(db):
    print(json.dumps(db, indent=4, sort_keys=True))

def dumpDB(name, db):
    if not os.path.exists('db'):
       os.makedirs('db')

    f = open("db/"+name,"w+")
    f.write(json.dumps(db, cls=DateTimeEncoder, indent=4, sort_keys=True))
    f.close()

def buildCloverDB():
    global cloverDB

    logFiles = glob.glob("log/node*.log")
    cloverDB = {}
    for f in logFiles:
        nodeName = re.search("node"+'.*',f).group(0)[0:-4]
        cloverDB[nodeName]={}
        cloverDB[nodeName]['log']=f

    for s in cloverDB:
        log = cloverDB[s]['log']

        #Build peers
        peers = os.popen("cat "+log+" | grep \"Added connection\"").readlines()
        peerDB = {}
        for p in peers:
            pEls=p.rstrip().split(' ')
            peerDB[pEls[5][5:]] = pEls[4].split(':')[0]
        cloverDB[s]['peers']=peerDB

        #Build transactions
        txs = os.popen("cat "+log+" | grep \"inv: tx\|proxytx\" | grep new").readlines()
        txDB = []
        for i in range(len(txs)):
            txData = txs[i].rstrip().split(' ')
        
            txTime = txData[0].replace('Z','').replace('T',' ') #txTime = AAAA-MM-DD HH:MM:SS
            if(txData[3]=='proxytx:'):
                isProxy=True
            else: isProxy=False
            if(isProxy):
                txDB.append({'tx':txData[4], 'time':txTime, 'source':txData[7][5:], 'proxy':isProxy, 'type':txData[6]})
        
        cloverDB[s]['txs']=txDB

    # printDB()
    dumpDB("clover.db",cloverDB)
    return cloverDB


def readFileLS(file):
    f = open(file, "r")

    fLines = f.readlines()

    for i in range(len(fLines)):
        fLines[i] = fLines[i].rstrip()

    f.close()
    
    return fLines

def getNodeByIP(ip):
    for n in nodeDB:
        if nodeDB[n] == ip:
            return n

def getNodeIP(node):
    return nodeDB[node]

def insertHop(path, hop):
   index=0
   # search
   for i in range(len(path)):
       if parseDate(hop['time']) < parseDate(path[i]['time']):
          break
       index+=1
   # Insertion
   path = path[:index] + [hop] + path[index:]
   return path

def getBrodcasted():
    broadcasted = []
    logs = os.popen("cat log/node*.log | grep \"Broadcasting proxytx\"").readlines()
    for tx in logs:
        tEls=tx.rstrip().split(' ')
        broadcasted.append(tEls[4])

    return broadcasted

def main():
    cloverDB=buildCloverDB()
    # printDB(cloverDB)

    # Parse nodeDB
    nodeList = readFileLS("db/nodes.db")
    global nodeDB
    nodeDB = {}
    for i in range(len(nodeList)):
        nodeList[i] = nodeList[i].split("=")
        nodeDB[nodeList[i][0]] = nodeList[i][1]

    # Parse txDB
    txs = readFileLS("db/txs.db")
    txDB = {}
    for i in range(len(txs)):
        txs[i] = txs[i].split(" ")
        if(txs[i][1] in nodeDB):
            txDB[txs[i][0]] = txs[i][1]
        else:
            print "WARNING: missing: "+txs[i][1]

    # Analyze transactions
    txsPath = {}
    #get broadcasted
    broadcastedTxs = getBrodcasted()

    for tx in txDB:
        txsPath[tx] = {}
        txsPath[tx]['SRC'] = txDB[tx]
        txsPath[tx]['path'] = []
        isBroadcasted = (tx in broadcastedTxs)
        # if tx in broadcasted:
        txsPath[tx]['broadcasted'] = isBroadcasted
        # else:

        #calculate path
        for n in cloverDB:
            for t in cloverDB[n]['txs']:
                if(t['tx'] == tx):
                    hop = {}
                    hop['node'] = n
                    hop['proxy'] = t['proxy']
                    hop['time'] = t['time']
                
                    txsPath[tx]['path'] = insertHop(txsPath[tx]['path'], hop)

        

    # printDB(txsPath)
    dumpDB("txPath.db",txsPath)

    # Calculate stats
    totHops = 0
    unbroadcast = 0

    txHops = {}
    for tx in txsPath:
        txHops[tx]={}
        proxyHops = 0
        broadcasted = False

        for h in txsPath[tx]['path']:
            if h['proxy'] == True: 
                proxyHops+=1       
        txHops[tx]['hops'] = proxyHops
        totHops+=proxyHops

        if tx in broadcastedTxs: 
            txHops[tx]['broadcast'] = True
        else:
            unbroadcast+=1
            print tx+" unbroadcast"

    dumpDB("txHops.db",txHops)
    avgHops = totHops / len(txsPath)
    print "Average proxy hops: "+str(avgHops)
    print "Unbroadcast transactions: "+str(unbroadcast)

    # txs per node
    nodeTxs={}
    for node in nodeList:
        nodeTxs[node[0]]={'txs':0,'inptxs':0,'outptxs':0}
    for tx in txDB:
        nodeTxs[txDB[tx]]['txs']+=1

    # inbound/outbound
    gRIn = 0
    gROut = 0
    gUOut = 0
    R=0
    U=0
    for node in cloverDB:
        if "Spy" in node: continue
        
        inptxs = 0
        outptxs = 0
        for tx in cloverDB[node]['txs']:
            if tx['proxy']==True:
                if tx['type']=="inbound":
                    nodeTxs[node]['inptxs']+=1
                else:
                    nodeTxs[node]['outptxs']+=1
        # print "inbound:"+str(inptxs)+" outbound:"+str(outptxs)
        if "U" in node:
            U+=1
            gUOut+=nodeTxs[node]['outptxs']
        else:
            R+=1
            gRIn+=nodeTxs[node]['inptxs']
            gROut+=nodeTxs[node]['outptxs']
        
    # printDB(nodeTxs)

    #TODO: avg produced transactions
    print "avg tx/node: "+str(float(len(txDB.keys()))/float(len(nodeDB.keys())))
    print "R: avg inbound="+str(gRIn/R)+" avg outbound="+str(gROut/R)
    if U>0:
        print "U: avg outbound="+str(gUOut/U)
        

main()