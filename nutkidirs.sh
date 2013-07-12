#!/bin/bash

while [ $# -gt 0 ]
do
    dir="$1"
    cd $dir
    pwd
    ../../nutki.sh $dir
    cd ..
    shift
done
