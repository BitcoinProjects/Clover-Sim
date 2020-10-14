import os
import time
import json
import fileinput
import threading

import btcnet

### TRANSACTIONS ###
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
        return

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

    if node == miner:
        return

    print("Funding "+node)
    balance = getBalance(miner)
    
    if balance > amount :
        sendTx(miner, node, amount)
    else:    
        print "Insufficient funds"
    
# Generate miner node
def addMiner():
    node=btcnet.getRandNode("node")
    miner=node+"Miner"
    os.system("docker rename "+node+" "+miner)

    #Update node DB file
    for line in fileinput.input("db/nodes.db", inplace = 1): 
      print line.replace(node+"=", miner+"="), # +"=" avoids ambiguity between R1 and R10

def getMiner():
    return btcnet.getRandNode("Miner")

# 
def generateTransactions(arg,stop_event):
    while not stop_event.is_set():
        nodes = btcnet.getRandList("node",2,"")
        txhash = sendTx(nodes[0], nodes[1], 0.00000001) #Send 1 satoshi
        txdb.write(txhash+" "+nodes[0]+" "+nodes[1]+"\n")
        time.sleep(1) #Generate a transactions every second()

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
    addMiner()

    global txdb
    txdb = open("db/txs.db", "w")

    # Create wallets #
    nodeList = btcnet.getNodeList()
    for node in nodeList:
        genBTCAddress(node)
        execWS(node, "settxfee 0.0")

    # Generate initial blocks
    genBlocks(110)
    time.sleep(60)

    # Send funds to all nodes #
    for node in nodeList:
        #send funds
        fundNode(node,2)
        time.sleep(1)

    # #Create block to confirm txs
    genBlocks(100)
    time.sleep(30)

def runTxSim(duration):
    global txdb
    txdb = open("db/txs.db", "a")

    #randomly generate transactions
    t_stop = threading.Event()
    thrTransactions = threading.Thread(target=generateTransactions, args=(1,t_stop))
    thrBlocks = threading.Thread(target=generateBlocks, args=(2,t_stop))
    thrTransactions.start()
    thrBlocks.start()

    #TODO Get simulation time as argument
    time.sleep(duration)
    t_stop.set()

    #TODO: save 'txrun' state. so that when new nodes are created, if txrun, send them coins