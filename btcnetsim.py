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
        epochTime = sys.argv[7]

        btcnet.createNetwork(int(numReach), int(numUnreach), numOutProxies, numInProxies, probDiffuse, epochTime)
        print("DONE\n")

        return

    # Delete the network
    if (sys.argv[1] == "delete"):
        btcnet.deleteNetwork()
        print("DONE\n")
        return

    # Generate transactions
    if (sys.argv[1] == 'txinit'):
        txgen.initTxSim()
        return

    if (sys.argv[1] == 'runsim'):
        #cleanup logs
        os.system("rm log/*")
        # nodeList = btcnet.getNodeList()
        # logFile="/root/.bitcoin/regtest/debug.log"
        # tmpFile="/root/.bitcoin/regtest/tmp.log"
        # for node in nodeList:
        #     os.system('docker exec -t '+node+' sh -c "cat '+logFile+' | grep \'Added connection\' > '+tmpFile+'"')
        #     os.system('docker exec -t '+node+' sh -c "mv '+tmpFile+' '+logFile+'"')
        #cleanup txs
        os.system("rm db/txs.db")

        duration = int(sys.argv[2])
        threads = duration = int(sys.argv[3])
        txgen.runTxSim(duration,threads)

        btcnet.dumpLogs()
        return

    # Generate transactions
    if (sys.argv[1] == 'txrun'):
        duration = int(sys.argv[2])
        threads = duration = int(sys.argv[3])
        txgen.runTxSim(duration,threads)
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
