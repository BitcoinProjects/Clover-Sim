import sys
import os
import time
import re
import glob
import json
import datetime

import btcnet
import txgen

spy="nodeSpy"
spylog="log/"+spy+".log"
spyRes="spy.db"

def parseDate(str):
    return datetime.datetime(int(str[0:4]),int(str[5:7]),int(str[8:10]),int(str[11:13]),int(str[14:16]),int(str[17:19]),int(str[20:26]))

class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime.datetime):
            return (str(z))
        else:
            return super().default(z)

def printDB():
    print(json.dumps(spyDB, indent=4, sort_keys=True))

def dumpDB(name, db):
    if not os.path.exists('db'):
       os.makedirs('db')

    f = open("db/"+name,"w+")
    f.write(json.dumps(db, cls=DateTimeEncoder, indent=4, sort_keys=True))
    f.close()

def buildSpyDB():
    global spyDB

    logFiles = glob.glob("log/"+spy+"*.log")
    spyDB = {}
    for f in logFiles:
        spyName = re.search(spy+'\d*',f).group(0)
        spyDB[spyName]={}
        spyDB[spyName]['log']=f

    for s in spyDB:
        log = spyDB[s]['log']

        #Build peers
        peers = os.popen("cat "+log+" | grep \"Added connection\"").readlines()
        peerDB = {}
        for p in peers:
            pEls=p.rstrip().split(' ')
            peerDB[pEls[5][5:]] = pEls[4].split(':')[0]
        spyDB[s]['peers']=peerDB

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
        spyDB[s]['txs']=txDB

    # printDB()
    dumpDB("spy.db",spyDB)

def estimateSources(printOutput):
    buildSpyDB()

    estSources = {}
    for s in spyDB:
        for t in spyDB[s]['txs']:
            if t not in estSources:
                estSources[t] = {}
                estSources[t]['src'] = spyDB[s]['peers'][spyDB[s]['txs'][t]['source']]
                estSources[t]['time'] = spyDB[s]['txs'][t]['time']
                estSources[t]['proxy'] = spyDB[s]['txs'][t]['proxy']
            elif parseDate(spyDB[s]['txs'][t]['time']) < parseDate(estSources[t]['time']):
                    estSources[t]['src'] = spyDB[s]['peers'][spyDB[s]['txs'][t]['source']]
                    estSources[t]['time'] = spyDB[s]['txs'][t]['time']
                    estSources[t]['proxy'] = spyDB[s]['txs'][t]['proxy']

    dumpDB("estSources.db",estSources)

    return estSources

# Make a node a spy
def addSpy(num):
    node=btcnet.getRandNode("node", "Miner")
   
    spyName = spy+str(num)
    btcnet.renameNode(node,spyName)

    #Connect to all nodes
    nodeList = btcnet.getNodeList("nodeR")
    for node in nodeList:
	    btcnet.connectNode(spyName,node)

def run(num_spies):
    for i in range(num_spies):
        addSpy(i)

def stop():
    if not os.path.exists('log'):
        os.makedirs('log')

    spyList = btcnet.getNodeList(spy)

    for s in spyList:
        nLog = os.popen('docker exec -t '+s+' cat /root/.bitcoin/regtest/debug.log').read()
        f = open("log/"+s+".log", "w")
        f.write(nLog)
        f.close()

    os.system("docker stop $(docker ps -a --filter=\"name="+spy+"\" -q) > /dev/null")
    os.system("docker rm $(docker ps -a --filter=\"name="+spy+"\" -q) > /dev/null")

def main():
    if(len(sys.argv)<2):
        return

    if not os.path.exists('firstspy'):
        os.makedirs('firstspy')

    if (sys.argv[1] == "run"):
        num_spies = 1
        if len(sys.argv)>2:
            num_spies = int(sys.argv[2])

        run(num_spies)
        print("DONE\n")

    if (sys.argv[1] == "stop"):
        stop()

    if (sys.argv[1] == "estimate"):
        estimateSources(True)

main()