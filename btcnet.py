
#################################################
#                                               #
# BTCNET: create and destroy network            #
#                                               #
#################################################

import os
import time
import math
import random

#Global
btcdir = "/btc/"
btcd = "bitcoind"
btcli = "bitcoin-cli"
btcdx = btcdir+btcd
btclix = btcdir+btcli

def getNodeIP(node):
    ip = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "+node).read().rstrip()

    return ip

def getNodeList(name):
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


#Create a docker image with the binaries contained in 'bindir' and save it as 'name'
def createNodeDock(bindir, name):
    os.system("docker run -it -d --name "+name+" ubuntu /bin/bash")
    os.system("docker cp "+bindir+" "+name+":/btc")
    os.system("docker commit "+name+" "+name+":latest")
    os.system("docker stop "+name+"&& docker rm "+name)

#Start a new node container
def runNode(img, name, options):
    print "Running "+name
    os.system("docker run -it -d --name "+name+" "+img+" "+btcdx+" -regtest "+options)

#Create 'numNodes' containers and create random connections
def createNetwork(bindir, name, numReach, numUnreach):
    createNodeDock(bindir, name)

    # numReach = int(math.ceil(numNodes / 10))+1
    # numUnreach = numNodes - numReach

    print "numReach="+str(numReach)+" numUnreach="+str(numUnreach)

    #create reachable nodes
    for i in range(1, numReach+1):
        runNode(name, "nodeR"+str(i), "-debug=net")

    #create unreachable nodes
    for i in range(1, numUnreach+1):
        runNode(name, "nodeU"+str(i), "-debug=net -listen=0")

    time.sleep(2)

    #create connections
    nodeList = getNodeList("node")
    for node in nodeList:
        #get random R nodes
        randList = getRandList("nodeR",3,node)

        print node+":"
        for rNode in randList:
            nodeIP = getNodeIP(rNode)
            print "add "+rNode+"("+nodeIP+")"
            # cmd='docker exec -t '+node+' '+btclix+' -regtest addnode '+ getNodeIP(rNode) +':18444 add'
            # print cmd
            os.system('docker exec -t '+node+' '+btclix+' -regtest addnode '+ getNodeIP(rNode) +':18444 add')

    return    

def deleteNetwork():
    os.system("docker stop $(docker ps -a --filter=\"name=node\" -q)")
    os.system("docker rm $(docker ps -a --filter=\"name=node\" -q)")

    return