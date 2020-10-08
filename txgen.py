import os
import time
import json

import btcnet

### TRANSACTIONS ###
#Global
wallet="netsim3"
miner=""

def execW(node, cmd):
    btcnet.execN(node, cmd, "-rpcwallet="+wallet)

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
    addr = getBTCAddress(nTo)
    execW(nFrom, "sendtoaddress "+addr+" "+str(amount))
    print "[LOG] Sent "+str(amount)+" from "+nFrom+" to "+nTo

# Generate 'num' blocks to 'nodeGiver'
def genBlocks(num):
    addr = getBTCAddress(miner)
    print "Generating "+str(num)+" blocks to "+miner
    execW(miner, "generatetoaddress "+str(num)+" "+addr+">/dev/null")

# Send funds to a node
def fundNode(node):
    print("Funding "+node)
    balance = getBalance(miner)
    print "Giver balance: "+ str(balance)
    
    #If there are no funds, create a new block
    if balance > 1 :
        sendTx(miner, node, 1)
    else:    
        print "Insufficient funds"
    
# Generate miner node
def addMiner():
    global miner

    node=btcnet.getRandNode("")
    print("randNode:"+node)
    miner=node+"Miner"
    os.system("docker rename "+node+" "+miner)

# Generate coins and transactions
#TODO: randomly generate blocks from different nodes
def generateTransactions():
    addMiner()

    nodeList = btcnet.getNodeList()

    # Create wallets #
    for node in nodeList:
        genBTCAddress(node)

    # Generate initial blocks
    genBlocks(101)
    time.sleep(30)

    for node in nodeList:
        print node+" blocks:"
        print str(execWR(node,"getblockcount") )

    # Send funds to all nodes #
    for node in nodeList:
        #send funds
        fundNode(node)
        time.sleep(1)

    # #Create block to confirm txs
    genBlocks(100)
    time.sleep(30)

    #for each node, check if they have funds
    nodeList = btcnet.getNodeList()
    for node in nodeList:
        balance = getBalance(node)
        # execW(node, "listtransactions")
        print "balance("+node+")="+str(balance)+" unconfirmed="+str(getUnconfirmedBalance(node))

    #collect addresses

    #randomly generate transactions

    #TODO: save 'txrun' state. so that when new nodes are created, if txrun, send them coins