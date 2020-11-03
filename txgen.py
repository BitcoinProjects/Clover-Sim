import os
import time
import json
import threading
# import math

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
    return addrs.keys()[0]

def getUnconfirmedBalance(node):
    balance = execWR(node, "getunconfirmedbalance")

    return float(balance)

def getBalance(node):
    balance = execWR(node, "getbalance")

    return float(balance)

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

    print("Funding "+node)
    balance = getBalance(miner)
    
    if balance > amount :
        sendTx(miner, node, amount)
    else:    
        print "Insufficient funds ("+str(balance)+")"
    
# Generate miner node
# def addMiner():
#     node=btcnet.getRandNode("nodeR")
#     miner=node+"Miner"

#     btcnet.renameNode(node,miner)

def getMiner():
    return btcnet.getRandNode("Miner")

# 
def generateTransactions(arg,stop_event):
    db = ""
    while not stop_event.is_set():
        nodes = btcnet.getRandList("node",2,"nodeMiner")
        txhash = sendTx(nodes[0], nodes[1], 0.00000001) #Send 1 satoshi
        if(txhash != None):
            db = db + txhash+" "+nodes[0]+" "+nodes[1]+"\n"
        # time.sleep(0.01) #Generate a transactions every 0.01 seconds
    txdb.write(db)

def generateBlocks(arg,stop_event):
    while not stop_event.is_set():
        print "Generating blocks"
        genBlocks(100)
        time.sleep(10) #Generate 100 blocks every 10 seconds

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
    # addMiner()

    # Create wallets #
    nodeList = btcnet.getNodeList()
    for node in nodeList:
        genBTCAddress(node)
        execWS(node, "settxfee 0.0")

    # Generate initial blocks
    genBlocks(110)
    time.sleep(30)

    # Send funds to all nodes #
    for node in nodeList:
        fundNode(node,1)
        time.sleep(1)

    #Create block to confirm txs
    genBlocks(101)
    time.sleep(100)

    for node in nodeList:
        print node+':'+str(getBalance(node))+' unconfirmed:'+str(getUnconfirmedBalance(node))


def runTxSim(duration):
    global txdb
    txdb = open("db/txs.db", "a+")

    #Generate blocks
    t_stop = threading.Event()
    thrBlocks = threading.Thread(target=generateBlocks, args=(2,t_stop))
    thrBlocks.start()
    
    #randomly generate transactions
    numThreads = int(round(len(btcnet.getNodeList())/10))
    if(numThreads==0): numThreads=1
    print "Starting "+str(numThreads)+" tx threads"
    for i in range(numThreads):
        thrTx = threading.Thread(target=generateTransactions, args=(1,t_stop))
        thrTx.start()

    #Stop simulation after 'duration'
    time.sleep(duration)
    t_stop.set()

    time.sleep(5)
    txdb.flush()
    txdb.close()

    numtxs = len(open("db/txs.db","r").readlines())
    print "Generated "+str(numtxs)+" transactions"

    #TODO: save 'txrun' state. so that when new nodes are created, if txrun, send them coins