#!/bin/bash
python btcnetsim.py create 30 50 1 5 30 \
&& python firstspy.py run 2 \
&& python btcnetsim.py txinit \
&& python btcnetsim.py txrun 120

python firstspy.py stop \
&& python btcnetsim.py delete 

python testEvaluator.py