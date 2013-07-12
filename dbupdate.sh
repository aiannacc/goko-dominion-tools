#/bin/bash

while [ $# -gt 0 ]
do
    echo "Day: $1"
    sleep 1

    BASE=http://dominionlogs.goko.com/$1/
    THREADS=20

    # Create log file directory
    cd "/mnt/raid/media/dominion/logs/"
    [ -d "$1" ] || mkdir "$1"
    cd "$1"
    [ -f "*.gz" ] && rm *.gz
    [ -f "_*" ] && rm _*

    # Get list of logs on server
    wget --header='Accept-Encoding: gzip' $BASE -O- 2>/dev/null |
        zcat | perl -lne 'print "$1" if /href="(.*?txt)"/' > _all
    echo "`cat _all | wc -l` logs on server"

    # Distinguish old logs vs. new
    ls > _old
    ls _* >> _old
    cat _all _old _old | sort | uniq -u > _new
    echo "Downloading `cat _new | wc -l` logs from server"

    # Download new logs in threads
    if [ `cat _new | wc -l` -gt 0 ]
    then
        cat _new | split -l 100 - _index.
        ls _index.* | xargs -n 1 -P $THREADS wget -nc \
            --base=$BASE --header='Accept-Encoding: gzip' -i 2>/dev/null
        rm _index.*
    fi

    # Clean up
    [ -f _all ] && rm _all
    [ -f _old ] && rm _old
    [ -f _new ] && rm _new

    # Parse new logs into database
    cd /home/ai/dominion/code/logparse/
    ./log2db.py /mnt/raid/media/dominion/logs/$1
    
    shift
done
