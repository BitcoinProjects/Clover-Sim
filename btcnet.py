
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

import txgen

#Global
IMG = "netsim"
btcdir = "/btc/"
bindir = "bin/"
btcd = "bitcoind"
btcli = "bitcoin-cli"
btcdx = btcdir+btcd
btclix = btcdir+btcli
btcopt = "-regtest -fallbackfee=0.00000001 -dustrelayfee=0.0 -debug=all"

def execN(node, cmd, opts=""):
    os.system("docker exec -t "+node+" "+btclix+" -regtest "+opts+" "+cmd)

def execS(node, cmd, opts=""):
    execN(node, cmd+">/dev/null", opts)

def execNR(node, cmd, opts=""):
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

def getRandNode(exclude):
    rList = getRandList("node",1,exclude)
    return rList[0]


#Create a docker image with the binaries contained in 'bin/' and save it as 'netsim'
def createNodeDock():
    os.system("docker run -it -d --name "+IMG+" ubuntu /bin/bash")
    os.system("docker cp "+bindir+" "+IMG+":/btc")
    os.system("docker commit "+IMG+" "+IMG+":latest")
    os.system("docker stop "+IMG+" && docker rm "+IMG)

#Start a new node container
def runNode(name, options):
    os.system("docker run -it -d --name "+name+" "+IMG+" "+btcdx+" "+btcopt+" "+options)
    print "Running "+name+"("+getNodeIP(name)+")"


def connectNode(nFrom,nTo):
    toAddr = getNodeIP(nTo)
    print "connecting "+nFrom+" to "+nTo
    execN(nFrom,"addnode "+toAddr+":18444 add")

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

    print "num nodes="+str(numReach+numUnreach)

    #create reachable nodes
    for i in range(1, numReach+1):
        runNode("nodeR"+str(i), "")

    #create unreachable nodes
    for i in range(1, numUnreach+1):
        runNode("nodeU"+str(i), "-listen=0")

    time.sleep(2)

    #create connections
    nodeList = getNodeList()
    for node in nodeList:
        connectNodes(node)

    return    

# Dump logs
def dumpLogs():
    if not os.path.exists('log'):
        os.makedirs('log')

    print "Dumping logs"

    nodeList = getNodeList()
    for node in nodeList:
        nLog = os.popen('docker exec -t '+node+' cat /root/.bitcoin/regtest/debug.log').read()

        f = open("log/"+node+".log", "w")
        f.write(nLog)
        f.close()

def stopNodes():
    nodeList = getNodeList()

    for node in nodeList:
        execS(node,"stop")

# Stop and delete all 'node' containers
def deleteNetwork():
    dumpLogs()

    os.system("docker stop $(docker ps -a --filter=\"name=node\" -q) > /dev/null")
    os.system("docker rm $(docker ps -a --filter=\"name=node\" -q) > /dev/null")
