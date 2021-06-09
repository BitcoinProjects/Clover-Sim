nodes=50
unreachable=0
time=600
threads=4

probDiffuse=

runSim(){
  type=$1
  numspies=$2
  numconnected=$3
  name=$4  

  echo "Running test $type$probDiffuse ($name) - nodes=$nodes - spies=$numspies (connected=$numconnected)"

  python btcnetsim.py create $type $nodes $unreachable $probDiffuse \
  && sleep 60 \
  && python firstspy.py run $numspies $numconnected \
  && python btcnetsim.py txinit \
  && python btcnetsim.py runsim $time $threads
  
  sleep 10

  python firstspy.py stop \
  && python btcnetsim.py delete 
 
  python testEvaluator.py > test/test-$type$probDiffuse.$name.txt  
}


runBatch(){
    type=$1
    connectSpy=$2

    ratios=( 1 2 5 10 20 30 )
    for r in "${ratios[@]}"
    do
        if [ "$r" -eq "5" ]; then
            nodes=60
        fi
        if [ "$r" -eq "1" ]; then
            sed -i -e 's/OUTPEERS=8/OUTPEERS=4/g' btcnet.py
            let numspies=1
        else
            let numspies=$nodes*$r/100
        fi

        if [ "$connectSpy" == "true" ]; then
            numconnected=numspies
        else
            numconnected=0
        fi
        
        for i in {1..3}
        do
            runSim $type $numspies $numconnected "$r-$i"
        done

        if [ "$r" -eq "1" ]; then
            sed -i -e 's/OUTPEERS=4/OUTPEERS=8/g' btcnet.py
        fi

        if [ "$r" -eq "5" ]; then
            nodes=50
        fi        
    done
}

type=$1

if [ "$type" == "clover" ]; then
    probs=( 10 20 30 )
    for p in "${probs[@]}"
    do
        echo "Running batch Clover (p=$p)"
        probDiffuse=$p
        runBatch $type "false"
    done
else
    echo "Running batch $type"
    runBatch $type "false"
fi

