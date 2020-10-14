import sys
import os
import time
import re
import glob
import json
import datetime

import btcnet

spy="spy"
spylog="log/"+spy+".log"
spyRes="spy.db"

def parseDate(str):
    return datetime.datetime(int(str[0:4]),int(str[5:7]),int(str[8:10]),int(str[11:13]),int(str[14:16]),int(str[17:19]))

class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime.datetime):
            return (str(z))
        else:
            return super().default(z)

def printDB():
    print(json.dumps(spyDB, indent=4, sort_keys=True))

def dumpDB():
    if not os.path.exists('db'):
       os.makedirs('db')

    f = open("db/spy.db","w+")
    f.write(json.dumps(spyDB, cls=DateTimeEncoder, indent=4, sort_keys=True))

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
        peers = os.popen("cat "+log+" | grep \"Added connection peer=\" | cut -d' ' -f4").readlines()
        addrs = os.popen("cat "+log+" | grep \"connection from\|trying connection\" | cut -d' ' -f4 | cut -d':' -f1").readlines()
        peerDB = {}
        for i in range(len(peers)):
            peerDB[peers[i].rstrip()[5:]] = addrs[i].rstrip()
        spyDB[s]['peers']=peerDB

        #Build transactions
        txs = os.popen("cat "+log+" | grep \"got inv: tx\" | grep new").readlines()
        txDB = {}
        txHashes = [None]*len(txs)
        txTimes = [None]*len(txs)
        txSources = [None]*len(txs)
        for i in range(len(txs)):
            txData = txs[i].rstrip().split(' ')
            txTime = txData[0].replace('Z','').replace('T',' ') #txTime = AAAA-MM-DD HH:MM:SS
            # txDate = parseDate(txTime) 
            # datetime.datetime(int(txTime[0:4]),int(txTime[5:7]),int(txTime[8:10]),int(txTime[10:12]),int(txTime[13:15]),int(txTime[16:18]))
            txDB[txData[4]] = {'time':txTime, 'source':txData[7][5:]}
        spyDB[s]['txs']=txDB

    # printDB()
    dumpDB()

def estimateSources(printOutput):
    buildSpyDB()

    estSources = {}
    for s in spyDB:
        for t in spyDB[s]['txs'].keys():
            if t not in estSources:
                estSources[t] = {}
                estSources[t]['src'] = spyDB[s]['peers'][spyDB[s]['txs'][t]['source']]
                estSources[t]['time'] = spyDB[s]['txs'][t]['time']
            else:
                if parseDate(spyDB[s]['txs'][t]['time']) < parseDate(estSources[t]['time']):
                    estSources[t]['src'] = spyDB[s]['peers'][spyDB[s]['txs'][t]['source']]
                    estSources[t]['time'] = spyDB[s]['txs'][t]['time']

    print estSources

    return estSources
    # f = open(spyRes+".db", "w")
    # f.write(nLog)
    # f.close()


def runSpyNode(num):
    spyName = spy+str(num)
    btcnet.runNode(spyName,"-debug=all")
    time.sleep(2)

    nodeList = btcnet.getNodeList()
    for node in nodeList:
        btcnet.connectNode(spyName,node)

def run(num_spies):
    for i in range(num_spies):
        runSpyNode(i)

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

    if (sys.argv[1] == "stop"):
        stop()

    if (sys.argv[1] == "estimate"):
        estimateSources(True)

main()
    #"got inv: tx a05aa67d30c76f2fac5e7083b1780f02839b293707593595b15af9b001963974  new peer=0"