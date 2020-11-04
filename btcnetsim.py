#################################################
#                                               #
# btcnetsim: main                               #
#                                               #
#################################################

import sys
from subprocess import Popen
import os
import json
import time
import random

import btcnet
import txgen

#Globals


def main():
    # Create the network
    if (sys.argv[1] == "create"):
        numReach = sys.argv[2]
        numUnreach = sys.argv[3]
        numOutProxies = sys.argv[4]
        numInProxies = sys.argv[5]
        probDiffuse = sys.argv[6]

        #Cleanup
        if not os.path.exists('log'):
            os.makedirs('log')
        else: os.system("rm log/*")
        if not os.path.exists('db'):
            os.makedirs('db')
        else: os.system("rm db/*")


        btcnet.createNetwork(int(numReach), int(numUnreach), numOutProxies, numInProxies, probDiffuse)

        return

    # Delete the network
    if (sys.argv[1] == "delete"):
        btcnet.deleteNetwork()
        return

    # Generate transactions
    if (sys.argv[1] == 'txinit'):
        txgen.initTxSim()
        return

    # Generate transactions
    if (sys.argv[1] == 'txrun'):
        duration = int(sys.argv[2])
        txgen.runTxSim(duration)
        return

    # Generate changes in the network
    if (sys.argv[1] == 'netrun'):
        return

    # Run external test script
    if (sys.argv[1] == 'testrun'):
        return

    else:
        print "\nUSAGE:\n"
        print "sudo python btcnetsim.py CMD [args]\n"
        print "CMDs:"
        print "create BINDIR REACH UNREACH : Create REACH reachable nodes and UNREACH unreachable nodes, using binaries in BINDIR."
        print "delete : Delete bitcoin blockchain."
        print "txrun: Make nodes generate random transactions."
        print "netrun: Generate random changes in the network."
        print "add BINDIR NUM: add NUM nodes using binaries in BINDIR."


main()
