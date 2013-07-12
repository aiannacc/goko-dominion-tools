#!/bin/bash

if [ $# -ne 1 ]
then
    echo Usage: nutki.sh [goko logdir]
    echo Example: nutki.sh 20130513
    exit -1
fi

BASE=http://dominionlogs.goko.com/$1/
THREADS=20

wget --header='Accept-Encoding: gzip' $BASE -O- | zcat | perl -lne 'print "$1" if /href="(.*?txt)"/' > _all
ls > _old
ls _* >> _old
cat _all _old | sort | uniq -u > _new

if [ `cat _new | wc -l` -gt 0 ]
then
    cat _new | split -l 100 - _index.
    ls _index.* | xargs -n 1 -P $THREADS wget --base=$BASE --header='Accept-Encoding: gzip' -i
    rm _index.*
    echo "Decompressing"
fi

for x in `cat _new`
do
    mv $x $x.gz
    gunzip $x.gz
done

rm _all
rm _old
rm _new
