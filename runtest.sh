#!/bin/bash
python btcnetsim.py create 10 5 2 2 30 30 \
&& python firstspy.py run 2 \
&& python btcnetsim.py txinit \
&& python btcnetsim.py txrun 120

python firstspy.py stop \
&& python btcnetsim.py delete 

python testEvaluator.py
python testClover.py

#!/bin/bash
python btcnetsim.py create 10 5 2 2 30 30 && python btcnetsim.py txinit && python firstspy.py run 2 && python btcnetsim.py txrun 120 && python firstspy.py stop && python btcnetsim.py delete && python testEvaluator.py && python testClover.py

#python btcnetsim.py create 20 10 2 2 30 30 && python firstspy.py run 1 && python btcnetsim.py txinit && python btcnetsim.py txrun 120 2 && python firstspy.py stop && python btcnetsim.py delete && python testEvaluator.py && python testClover.py