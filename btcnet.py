
#################################################
#                                               #
# BTCNET: create and destroy network            #
#                                               #
#################################################

import os
import time
import math
import random
import json
import fileinput

import txgen

#Global
IMG = "netsim"
miner="nodeMiner"
btcdir = "/btc/"
bindir = "bin/"
btcd = "bitcoind"
btcli = "bitcoin-cli"
btcdx = btcdir+btcd
btclix = btcdir+btcli
btcopt = "-regtest -fallbackfee=0.00000001 -dustrelayfee=0.0 -logips -debug=all -logtimemicros"

def execN(node, cmd, opts=""):
    os.system("docker exec -t "+node+" "+btclix+" -regtest "+opts+" "+cmd)

def execS(node, cmd, opts=""):
    execN(node, cmd+">/dev/null", opts)

def execNR(node, cmd, opts=""):
    assert(node != None)
    assert(cmd != None)
    return os.popen("docker exec -t "+node+" "+btclix+" -regtest "+opts+" "+cmd).read().strip()

def getNodeIP(node):
    ip = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "+node).read().rstrip()

    return ip

def getNodeList(name="node"):
    nodeList = os.popen("docker ps --filter=\"name="+name+"\" --format '{{.Names}}'").readlines()
    for i in range(len(nodeList)):
        nodeList[i] = nodeList[i].rstrip()

    return nodeList

def getRandList(name, num, exclude):
    randList = getNodeList(name)
    #remove 'exclude
    if exclude in randList:
        randList.remove(exclude)
    #shuffle
    random.shuffle(randList)
    #get first num elements
    del randList[num:]

    return randList

def getRandNode(name, exclude=""):
    rList = getRandList(name,1,exclude)
    if(len(rList)>0):
        return rList[0]


#Create a docker image with the binaries contained in 'bin/' and save it as 'netsim'
def createNodeDock():
    os.system("docker run -it -d --name "+IMG+" ubuntu:latest /bin/bash")
    os.system("docker cp "+bindir+" "+IMG+":/btc")
    os.system("docker commit "+IMG+" "+IMG+":node")
    os.system("docker stop "+IMG+" && docker rm "+IMG)

def createNodeMiner():    
    os.system("docker run -it -d --name "+miner+" ubuntu:latest /bin/bash")
    os.system("docker cp "+"bin020/"+" "+miner+":/btc")
    os.system("docker commit "+miner+" "+IMG+":miner")
    os.system("docker stop "+miner+" && docker rm "+miner)

#Start a new node container
def runMiner():
    os.system("docker run -it -d --name "+miner+" "+IMG+":miner "+btcdx+" "+btcopt)
    print "Running "+miner+"("+getNodeIP(miner)+")"

    if not os.path.exists('db'):
        os.makedirs('db')

    nodeDb = open("db/nodes.db","a")
    nodeDb.write(miner+"="+getNodeIP(miner)+"\n")

#Start a new node container
def runNode(name, options):
    os.system("docker run -it -d --name "+name+" "+IMG+":node "+btcdx+" "+btcopt+" "+options)
    print "Running "+name+"("+getNodeIP(name)+")"

    if not os.path.exists('db'):
        os.makedirs('db')

    nodeDb = open("db/nodes.db","a")
    nodeDb.write(name+"="+getNodeIP(name)+"\n")

def renameNode(name, newName):
    os.system("docker rename "+name+" "+newName)

    #Update node DB file
    for line in fileinput.input("db/nodes.db", inplace = 1): 
      print line.replace(name+"=", newName+"="), # +"=" avoids ambiguity between R1 and R10


def connectNode(nFrom,nTo):
    toAddr = getNodeIP(nTo)
    print "connecting "+nFrom+" to "+nTo
    execN(nFrom,"addnode "+toAddr+":18444 onetry")

#Connect a node to 3 R nodes
def connectNodes(node):
    #get random R nodes
    randList = getRandList("nodeR",8,node)

    print node+":"
    for rNode in randList:
        connectNode(node,rNode)

#Run a new node and connect it
def addNode(name, options):
    runNode(name, options)
    time.sleep(2)
    connectNodes(name)

#Create 'numReach'+'numUnreach' containers and create random connections
def createNetwork(numReach, numUnreach):
    createNodeDock()
    createNodeMiner()

    print "num nodes="+str(numReach+numUnreach)

    #create reachable nodes
    for i in range(1, numReach+1):
        runNode("nodeR"+str(i), "")

    #create unreachable nodes
    for i in range(1, numUnreach+1):
        runNode("nodeU"+str(i), "-listen=0")

    #create miner
    runMiner()

    time.sleep(2)

    #create connections
    nodeList = getNodeList()
    for node in nodeList:
        connectNodes(node)

    return    

# Dump logs
def dumpLogs():
    print "Dumping logs"

    nodeList = getNodeList()
    for node in nodeList:
        nLog = os.popen('docker exec -t '+node+' cat /root/.bitcoin/regtest/debug.log').read()

        f = open("log/"+node+".log", "w")
        f.write(nLog)
        f.close()

def stopContainers(name):
    print "Stopping "+name+" containers"
    os.system("docker stop $(docker ps -a --filter=\"name="+name+"\" -q) > /dev/null")
    os.system("docker rm $(docker ps -a --filter=\"name="+name+"\" -q) > /dev/null")

def stopNodes():
    nodeList = getNodeList()

    for node in nodeList:
        execS(node,"stop")

# Stop and delete all 'node' containers
def deleteNetwork():
    dumpLogs()
    stopContainers("node")