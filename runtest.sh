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
python btcnetsim.py create 10 5 2 2 30 30 && python btcnetsim.py txinit && python firstspy.py run 2 1 && python btcnetsim.py txrun 120 && python firstspy.py stop && python btcnetsim.py delete && python testEvaluator.py && python testClover.py

#python btcnetsim.py create 100 0 2 2 20 30 && python firstspy.py run 10 3 && python btcnetsim.py txinit && python btcnetsim.py txrun 500 4 ; python firstspy.py stop && python btcnetsim.py delete ; python testEvaluator.py && python testClover.py