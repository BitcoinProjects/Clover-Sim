import os
import time
import json
import threading
import datetime

import btcnet

#Global
wallet="netsim3"

def execW(node, cmd):
    btcnet.execN(node, cmd, "-rpcwallet="+wallet)

def execWS(node, cmd):
    btcnet.execS(node, cmd, "-rpcwallet="+wallet)

def execWR(node, cmd):
    return btcnet.execNR(node, cmd, "-rpcwallet="+wallet)

# Generate node's Bitcoin address
def genBTCAddress(node):
    btcnet.execS(node,"createwallet "+wallet)
    return execWR(node,"getnewaddress")

# Returns node's Bitcoin address
def getBTCAddress(node):
    addrs = json.loads(execWR(node," getaddressesbylabel \"\""))
    if addrs.keys() > 0:
        return addrs.keys()[0]
    else: return None

def getUnconfirmedBalance(node):
    balance = execWR(node, "getunconfirmedbalance")

    return float(balance)

def getBalance(node):
    balance = execWR(node, "getbalance")

    try:
      ret = float(balance)
    except:
      print("ERR:"+balance)
      ret = -1

    return ret

# Send a transaction from node 'nFrom' to address 'nTo' with 'amount' coins
def sendTx(nFrom, nTo, amount):
    print "[LOG] Sending "+str(amount)+" from "+nFrom+" to "+nTo

    balance = getBalance(nFrom)
    if balance < amount:
        print("ERR: can't send tx: insufficient balance")
        return None

    addr = getBTCAddress(nTo)
    txhash=execWR(nFrom, "sendtoaddress "+addr+" "+str(amount))

    return txhash

# Generate 'num' blocks to 'nodeGiver'
def genBlocks(num):
    miner=getMiner()
    addr = getBTCAddress(miner)
    print "[LOG] Generating "+str(num)+" blocks to "+miner
    execW(miner, "generatetoaddress "+str(num)+" "+addr+">/dev/null")

# Send funds to a node
def fundNode(node,amount):
    miner=getMiner()
    if miner == None:
        print "ERROR: No miner found"
        return 

    if node == miner:
        return

    # balance = getBalance(miner)
    # print "balance: "+str(balance)
    # if balance > amount :
        # sendTx(miner, node, amount)
    # else:    
    #     print "Insufficient funds ("+str(balance)+")"

    try:
      sendTx(miner, node, amount)
    except:
        print "ERROR: could not send tx"
    
def addMiner():
    node = btcnet.getRandNode("nodeR")
    print "Making "+node+" a miner"
    btcnet.renameNode(node,"nodeMiner")

def getMiner():
    return btcnet.getRandNode("Miner")

# 
lastTx = {}
mutex = threading.Lock()
def generateTransactions(arg,stop_event):
    db = ""
    nodeList = btcnet.getNodeList()
    global lastTx
    global mutex
    for n in nodeList:
        lastTx[n] = datetime.datetime.now() - datetime.timedelta(seconds=5)

    while not stop_event.is_set():
        nodes = btcnet.getRandList("node",2,"Spy")
        #Only use node if no other thread is working on it
        if nLocks[nodes[0]].acquire(False):
            # only generate 1 tx per second for each node
            if datetime.datetime.now() < lastTx[nodes[0]] + datetime.timedelta(seconds=5):
                continue

            mutex.acquire()
            try:
                txhash = sendTx(nodes[0], nodes[1], 0.00000001) #Send 1 satoshi
            except:
                print "ERROR: could not send tx"
            mutex.release()
            if(txhash != None):
                db = db + txhash+" "+nodes[0]+" "+nodes[1]+"\n"
            lastTx[nodes[0]] = datetime.datetime.now()
            # time.sleep(0.1) #Generate a transactions every 0.01 seconds

            nLocks[nodes[0]].release()

    txdb.write(db)
    txdb.flush()

def generateBlocks(arg,stop_event):
    while not stop_event.is_set():
        print "Generating blocks"
        genBlocks(101)
        time.sleep(30) #Generate 101 blocks every 30 seconds

        #TODO: check if any node need funds
        # fundNode(node,amount)

def printBalances():
    nodeList = btcnet.getNodeList()
    for node in nodeList:
        balance = getBalance(node)
        print "balance("+node+")="+str(balance)+" unconfirmed="+str(getUnconfirmedBalance(node))

# Generate coins and transactions
#TODO: randomly generate blocks from different nodes
def initTxSim():
    addMiner()

    # Create wallets #
    print "Create wallets..."
    nodeList = btcnet.getNodeList()
    for node in nodeList:
        if "Spy" in node: continue
        print "Initiating "+node
        genBTCAddress(node)
        execWS(node, "settxfee 0.0")

    # Generate initial blocks
    genBlocks(110)
    time.sleep(30)

    # Send funds to all nodes #
    for node in nodeList:
        if "Spy" in node or "Miner" in node: continue

        try:
            fundNode(node,3)
        except:
            #try 2 times
            time.sleep(0.5)
            fundNode(node,3)
        time.sleep(0.2)
    time.sleep(30)

    #Create block to confirm txs
    genBlocks(110)
    time.sleep(30)

    # for node in nodeList:
    #     print node+':'+str(getBalance(node))+' unconfirmed:'+str(getUnconfirmedBalance(node))


def runTxSim(duration,threads):
    global txdb
    txdb = open("db/txs.db", "a")

    #Generate blocks
    t_stop = threading.Event()
    thrBlocks = threading.Thread(target=generateBlocks, args=(2,t_stop))
    thrBlocks.start()
    global nLocks
    nLocks = {}
    nodeList = btcnet.getNodeList(exclude="Spy")
    for n in nodeList:
        nLocks[n] = threading.RLock()
    
    #randomly generate transactions
    numThreads = threads
    print "Starting "+str(numThreads)+" tx threads"
    threads=[]
    for i in range(numThreads):
        thrTx = threading.Thread(target=generateTransactions, args=(1,t_stop))
        thrTx.start()
        threads.append(thrTx)

    #Stop simulation after 'duration'
    time.sleep(duration)
    t_stop.set()

    for t in threads:
        t.join()

    txdb.close()

    txdb=open("db/txs.db","r")
    numtxs = len(txdb.readlines())
    print "Generated "+str(numtxs)+" transactions"
    txdb.close()

    #TODO: save 'txrun' state. so that when new nodes are created, if txrun, send them coins