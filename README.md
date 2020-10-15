# btcnetsim
Bitcoin Network Simulator using regtest and docker containers [work in progress]

Currently does:
  - Create network with N reachable nodes and M unreachable nodes  
  - Connect each node to 8 outbound peers  
  - Create a miner from existing nodes, initialize blockchain, and fund existing nodes with 1 BTC  
  - Run simulation for X seconds, continuously creating micro transactions and 100 blocks every 10 seconds
    - Transactions transfer 1 satoshi between 2 random nodes of the network  
    - One independent thread is run for every 10 nodes in the network (e.g., 40 nodes imply 4 threads)

## Requirements
  - Python 2.7
  - Docker

## Usage
   `python btcnetsim.py [create|txinit|txrun|delete]`

   - `create NUM_REACHABLE NUM_UNREACHABLE`
   - `txinit` : create miner node, generate 101 blocks, send 1 BTC to each node
   - `txrun` SECONDS : create a 1-sat transaction every second between two random nodes
   - `delete` : dump nodes logs (debug.log) and delete all 'node' containers
    
   Example:
   `python btcnetsim.py create 10 10 && python btcnetsim.py txinit && python btcnetsim.py txrun 60 ; python btcnetsim.py delete`