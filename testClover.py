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
        txs = os.popen("cat "+log+" | grep new | grep \"got inv: tx\|got proxytx\"").readlines()
        txDB = {}
        for i in range(len(txs)):
            txData = txs[i].rstrip().split(' ')
            if(txData[4] not in txDB.keys()):
                # print txData
                txTime = txData[0].replace('Z','').replace('T',' ') #txTime = AAAA-MM-DD HH:MM:SS
                if(txData[3]=='proxytx:'):
                    isProxy=True
                else: isProxy=False
                txDB[txData[4]] = {'time':txTime, 'source':txData[7][5:], 'proxy':isProxy}
        cloverDB[s]['txs']=txDB

    # printDB()
    dumpDB("clover.db",cloverDB)


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

def main():
    buildCloverDB()
    # printDB(cloverDB)

    # Parse nodeDB
    nodes = readFileLS("db/nodes.db")
    global nodeDB
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

    # Analyze transactions
    txsPath = {}
    for tx in txDB:
        txsPath[tx] = {}
        txsPath[tx]['SRC'] = getNodeByIP(txDB[tx])
        txsPath[tx]['path'] = []

        #calculate path
        for n in cloverDB:
            if tx in cloverDB[n]['txs']:
                # print cloverDB[n]['txs'][tx]
                h = cloverDB[n]['txs'][tx]
                hop = {}
                hop['node'] = n
                # hop['from'] = getNodeByIP(cloverDB[n]['peers'][h['source']])
                hop['proxy'] = h['proxy']
                hop['time'] = h['time']
            
                txsPath[tx]['path'] = insertHop(txsPath[tx]['path'], hop)

    printDB(txsPath)
    dumpDB("txPath.db",txsPath)

main()