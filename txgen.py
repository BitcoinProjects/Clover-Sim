import os
import time
import json
import threading

import btcnet

### TRANSACTIONS ###
#Global
wallet="netsim3"
miner=""
do_run=True

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
        return

    addr = getBTCAddress(nTo)
    execW(nFrom, "sendtoaddress "+addr+" "+str(amount))

# Generate 'num' blocks to 'nodeGiver'
def genBlocks(num):
    addr = getBTCAddress(miner)
    print "[LOG] Generating "+str(num)+" blocks to "+miner
    execW(miner, "generatetoaddress "+str(num)+" "+addr+">/dev/null")

# Send funds to a node
def fundNode(node,amount):
    if node == miner:
        return

    print("Funding "+node)
    balance = getBalance(miner)
    print "Giver balance: "+ str(balance)
    
    #If there are no funds, create a new block
    if balance > amount :
        sendTx(miner, node, amount)
    else:    
        print "Insufficient funds"
    
# Generate miner node
def addMiner():
    global miner

    node=btcnet.getRandNode("")
    print("randNode:"+node)
    miner=node+"Miner"
    os.system("docker rename "+node+" "+miner)


# 
def generateTransactions(arg,stop_event):
    while not stop_event.is_set():
        nodes = btcnet.getRandList("node",2,"")
        sendTx(nodes[0], nodes[1], 0.00000001) #Send 1 satoshi
        time.sleep(1) #Generate a transactions every second()

def generateBlocks(arg,stop_event):
    while not stop_event.is_set():
        print "Generating blocks"
        genBlocks(100)

        # Send some funds to nodes #
        nodeList = btcnet.getNodeList()
        for node in nodeList:
            #send funds
            fundNode(node,1)

        time.sleep(10) #Generate 100 blocks every 10 seconds

def printBalances():
    nodeList = btcnet.getNodeList()
    for node in nodeList:
        balance = getBalance(node)
        # execW(node, "listtransactions")
        print "balance("+node+")="+str(balance)+" unconfirmed="+str(getUnconfirmedBalance(node))

# Generate coins and transactions
#TODO: randomly generate blocks from different nodes
def initTxSim():
    addMiner()

    nodeList = btcnet.getNodeList()

    # Create wallets #
    for node in nodeList:
        genBTCAddress(node)
        execWS(node, "settxfee 0.0")

    # Generate initial blocks
    genBlocks(101)
    time.sleep(30)

    # Send funds to all nodes #
    for node in nodeList:
        #send funds
        fundNode(node,1)
        time.sleep(1)

    # #Create block to confirm txs
    genBlocks(100)
    time.sleep(30)

    #randomly generate transactions
    t_stop = threading.Event()
    thrTransactions = threading.Thread(target=generateTransactions, args=(1,t_stop))
    thrBlocks = threading.Thread(target=generateBlocks, args=(2,t_stop))
    thrTransactions.start()
    thrBlocks.start()

    #TODO Get simulation time as argument
    time.sleep(30)
    t_stop.set()

    printBalances()

    #TODO: save 'txrun' state. so that when new nodes are created, if txrun, send them coins