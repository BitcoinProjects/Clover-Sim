import sys
import os
import time
import btcnet

spy="spy"
spylog="log/"+spy+".log"
spyRes="spy.db"

def estimateSources(printOutput):
    # build peer list
    peers=os.popen("cat "+spylog+" | grep \"Added connection peer=\" | cut -d' ' -f4").readlines()
    addrs = os.popen("cat "+spylog+" | grep \"connection from\|trying connection\" | cut -d' ' -f4 | cut -d':' -f1").readlines()

    peerDB = {}
    for i in range(1,len(peers)):
        peerDB[peers[i].rstrip()]=addrs[i].rstrip()

    # for p in peerDB:
    #     print p+"  "+peerDB[p]

    # associate tx to the first peer to send it to us
    txs=os.popen("cat "+spylog+" | grep \"got inv: tx\" | grep new | cut -d' ' -f5").readlines()
    sources=os.popen("cat "+spylog+" | grep \"got inv: tx\" | grep new | cut -d' ' -f8").readlines()

    txDB = {}
    for i in range(1,len(txs)):
        txDB[txs[i].rstrip()]=sources[i].rstrip()

    estSources = {}
    for t in txDB:
        if txDB[t] in peerDB:
            if(printOutput):
                print t+"  "+peerDB[txDB[t]]
            estSources[t]=peerDB[txDB[t]]

    return estSources
    # f = open(spyRes+".db", "w")
    # f.write(nLog)
    # f.close()


def run():
    btcnet.runNode(spy,"-debug=all")
    time.sleep(2)

    nodeList = btcnet.getNodeList()
    for node in nodeList:
        btcnet.connectNode(spy,node)
        #TODO: connectNode(spy,node) x3

    # btcnet.execN(spy,"getpeerinfo | grep addr")

def stop():
    nLog = os.popen('docker exec -t '+spy+' cat /root/.bitcoin/regtest/debug.log').read()

    f = open("log/"+spy+".log", "w")
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
        run()

    if (sys.argv[1] == "stop"):
        stop()

    if (sys.argv[1] == "estimate"):
        estimateSources(True)

main()
    #"got inv: tx a05aa67d30c76f2fac5e7083b1780f02839b293707593595b15af9b001963974  new peer=0"